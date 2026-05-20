"""Spring solver orchestration."""

from __future__ import annotations

from .errors import SpringSizingError
from .generation import run_search
from .geometry import derive_search_geometry
from .mass_budget import compute_mass_budget
from .models import (
    DomainModel,
    MassBudgetResult,
    ResolvedSpringPayload,
    SpringForceTargets,
    SpringSearchDiagnosticsPayload,
    SpringSearchGeometry,
    SpringSizingConfig,
    SpringSolverInputs,
)
from .targets import resolve_force_targets
from .tokens import (
    SPRING_SOLVER_STATUS_COMPUTED,
    SPRING_SOLVER_STATUS_MASS_BUDGET_ONLY,
    SPRING_SOLVER_STATUS_NO_CANDIDATES,
    SPRING_SOLVER_STATUS_NO_STRICT_FIT_CANDIDATES,
)


class PreparedSolverContext(DomainModel):
    spring_sizing_cfg: SpringSizingConfig
    spring_count: int
    mass_budget: MassBudgetResult
    geometry: SpringSearchGeometry
    force_targets: SpringForceTargets


class SpringPreparation(DomainModel):
    mass_budget: MassBudgetResult
    context: PreparedSolverContext | None


def prepare_solver_context(*, spring_inputs: SpringSolverInputs) -> SpringPreparation:
    cap_volume_mm3 = spring_inputs.cap_volume_mm3
    if cap_volume_mm3 is None:
        raise SpringSizingError("cap_volume_mm3 is required for spring sizing")
    mass_budget = compute_mass_budget(
        mass_budget_cfg=spring_inputs.mass_budget,
        cap_volume_mm3=cap_volume_mm3,
    )

    spring_sizing_cfg = spring_inputs.spring_sizing
    if spring_sizing_cfg is None:
        return SpringPreparation(mass_budget=mass_budget, context=None)

    spring_count = spring_sizing_cfg.spring_count
    if spring_count < 1:
        raise SpringSizingError("spring_sizing.spring_count must be >= 1")
    if spring_count != spring_inputs.geometry.spring_count:
        raise SpringSizingError(
            "spring_sizing.spring_count must match spring_inputs.geometry.spring_count "
            f"({spring_count} != {spring_inputs.geometry.spring_count})"
        )

    geometry = derive_search_geometry(
        geometry_inputs=spring_inputs.geometry,
        spring_sizing_cfg=spring_sizing_cfg,
    )
    force_targets = resolve_force_targets(
        spring_sizing_cfg=spring_sizing_cfg,
        spring_count=spring_count,
        switch_force_nominal_n=spring_sizing_cfg.switch_force_nominal_n,
        mass_budget=mass_budget,
    )

    return SpringPreparation(
        mass_budget=mass_budget,
        context=PreparedSolverContext(
            spring_sizing_cfg=spring_sizing_cfg,
            spring_count=spring_count,
            mass_budget=mass_budget,
            geometry=geometry,
            force_targets=force_targets,
        ),
    )


def resolve_spring(
    *,
    name: str,
    spring_inputs: SpringSolverInputs,
) -> SpringSearchDiagnosticsPayload | None:
    if spring_inputs.mass_budget is None and spring_inputs.spring_sizing is None:
        return None

    preparation = prepare_solver_context(spring_inputs=spring_inputs)
    mass_budget = preparation.mass_budget
    context = preparation.context

    if context is None:
        return SpringSearchDiagnosticsPayload(
            status=SPRING_SOLVER_STATUS_MASS_BUDGET_ONLY,
            name=name,
            mass_budget=mass_budget,
        )

    first_pass = run_search(
        spring_count=context.spring_count,
        spring_sizing_cfg=context.spring_sizing_cfg,
        geometry=context.geometry,
        force_targets=context.force_targets,
        wire_diameters_mm=context.spring_sizing_cfg.allowed_wire_diameters_default_mm,
    )
    if first_pass.ranked_candidates:
        search_result = first_pass
    else:
        expanded_wire_diameters_mm = list(
            dict.fromkeys(
                context.spring_sizing_cfg.allowed_wire_diameters_default_mm
                + context.spring_sizing_cfg.allowed_wire_diameters_extended_mm
            )
        )
        search_result = run_search(
            spring_count=context.spring_count,
            spring_sizing_cfg=context.spring_sizing_cfg,
            geometry=context.geometry,
            force_targets=context.force_targets,
            wire_diameters_mm=expanded_wire_diameters_mm,
        )

    active_candidate = search_result.ranked_candidates[0] if search_result.ranked_candidates else None
    resolved_spring = (
        ResolvedSpringPayload(active_candidate=active_candidate)
        if active_candidate is not None
        else None
    )

    status = (
        SPRING_SOLVER_STATUS_COMPUTED
        if search_result.ranked_candidates
        else (
            SPRING_SOLVER_STATUS_NO_STRICT_FIT_CANDIDATES
            if search_result.near_miss_candidates
            else SPRING_SOLVER_STATUS_NO_CANDIDATES
        )
    )
    return SpringSearchDiagnosticsPayload(
        status=status,
        name=name,
        mass_budget=mass_budget,
        spring_sizing=context.spring_sizing_cfg,
        force_targets=context.force_targets,
        geometry=context.geometry,
        resolved=resolved_spring,
        top_candidates=search_result.ranked_candidates[: context.spring_sizing_cfg.diagnostics_top_k],
        near_miss_candidates=search_result.near_miss_candidates[
            : context.spring_sizing_cfg.diagnostics_top_k
        ],
        reject_reason_histogram=search_result.reject_reason_histogram,
    )
