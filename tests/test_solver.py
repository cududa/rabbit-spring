from __future__ import annotations

import math

import pytest

from rabbit_spring import (
    ForceBand,
    MassBudgetConfig,
    MassBudgetFixedItemConfig,
    SpringGeometryInputs,
    SpringSizingConfig,
    SpringSolveRequest,
    SpringSolverInputs,
    SpringSupportAnnulus,
    solve_spring,
)
from rabbit_spring.errors import SpringSizingError
from rabbit_spring.geometry import derive_search_geometry
from rabbit_spring.mass_budget import compute_mass_budget
from rabbit_spring.models import (
    CandidateFit,
    CandidatePhysics,
    ScoreWeights,
    SpringForceTargets,
    SpringSearchGeometry,
)
from rabbit_spring.score import score_candidate
from rabbit_spring.targets import resolve_force_targets
from rabbit_spring.tokens import (
    SPRING_REJECT_FORCE_ACTUATION_NON_POSITIVE,
    SPRING_SOLVER_STATUS_COMPUTED,
    SPRING_SOLVER_STATUS_NO_CANDIDATES,
    SPRING_WARN_EXPLORATORY_WIRE_DIAMETER,
    SPRING_WARN_SOLID_MARGIN_BELOW_PREFERRED,
    SPRING_WARN_SPRING_INDEX_OUTSIDE_PREFERRED,
    SPRING_WARN_STRESS_ABOVE_SOFT_WARN,
    SPRING_WARN_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_PREFERRED,
    SPRING_WARN_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_PREFERRED,
)
from rabbit_spring.fit import evaluate_candidate_fit


def _geometry_inputs() -> SpringGeometryInputs:
    return SpringGeometryInputs(
        spring_count=3,
        post_outer_diameter_mm=2.0,
        support_annulus=SpringSupportAnnulus(
            inner_diameter_mm=4.4,
            outer_diameter_mm=6.0,
        ),
        well_inner_diameter_mm=6.45,
        spring_top_interface_world_z_mm=8.0,
        well_floor_z_world_mm=1.0,
        actuation_travel_delta_mm=0.5,
        compressed_hard_stop_travel_delta_mm=1.0,
    )


def _solver_inputs(
    *,
    cap_volume_mm3: float = 2000.0,
    spring_sizing: SpringSizingConfig | None = None,
) -> SpringSolverInputs:
    return SpringSolverInputs(
        geometry=_geometry_inputs(),
        cap_volume_mm3=cap_volume_mm3,
        mass_budget=MassBudgetConfig(
            fixed_items=[MassBudgetFixedItemConfig(name="steel_rods", mass_g=2.0)]
        ),
        spring_sizing=spring_sizing or SpringSizingConfig(spring_count=3),
    )


def make_solver_inputs(
    *,
    cap_volume_mm3: float = 2000.0,
    spring_sizing: SpringSizingConfig | None = None,
) -> SpringSolverInputs:
    return _solver_inputs(cap_volume_mm3=cap_volume_mm3, spring_sizing=spring_sizing)


def _search_geometry() -> SpringSearchGeometry:
    return SpringSearchGeometry(
        post_outer_diameter_mm=2.0,
        support_annulus=SpringSupportAnnulus(inner_diameter_mm=4.4, outer_diameter_mm=6.0),
        well_inner_diameter_mm=6.45,
        spring_top_interface_world_z_mm=8.0,
        well_floor_z_world_mm=1.0,
        installed_length_rest_mm=7.0,
        installed_length_actuation_mm=6.5,
        installed_length_compressed_hard_stop_mm=6.0,
    )


def test_solve_spring_computes_candidate() -> None:
    result = solve_spring(SpringSolveRequest(name="demo", inputs=_solver_inputs()))

    assert result.diagnostics.status == SPRING_SOLVER_STATUS_COMPUTED
    assert result.diagnostics.resolved is not None
    assert result.diagnostics.top_candidates

    candidate = result.diagnostics.resolved.active_candidate
    assert math.isclose(
        candidate.physics.solid_height_mm,
        candidate.physics.total_coils * candidate.geometry.wire_diameter_mm,
    )
    assert candidate.installed_length_rest_mm > candidate.installed_length_actuation_mm
    assert candidate.installed_length_actuation_mm > candidate.installed_length_compressed_hard_stop_mm


def test_search_expands_to_extended_wire_list() -> None:
    result = solve_spring(
        SpringSolveRequest(
            name="extended",
            inputs=_solver_inputs(
                spring_sizing=SpringSizingConfig(
                    spring_count=3,
                    allowed_wire_diameters_default_mm=[0.5],
                    allowed_wire_diameters_extended_mm=[0.30],
                    mean_diameter_candidates_mm=[5.10],
                    active_coils_min=3,
                    active_coils_max=3,
                )
            ),
        )
    )

    assert result.diagnostics.status == SPRING_SOLVER_STATUS_COMPUTED
    assert result.diagnostics.resolved is not None
    assert result.diagnostics.resolved.active_candidate.geometry.wire_diameter_mm == 0.30


def test_mass_budget_adjusts_force_targets() -> None:
    cfg = SpringSizingConfig(spring_count=3)
    light = compute_mass_budget(mass_budget_cfg=MassBudgetConfig(), cap_volume_mm3=2000.0)
    heavy = compute_mass_budget(mass_budget_cfg=MassBudgetConfig(), cap_volume_mm3=250000.0)

    light_targets = resolve_force_targets(
        spring_sizing_cfg=cfg,
        spring_count=3,
        switch_force_nominal_n=cfg.switch_force_nominal_n,
        mass_budget=light,
    )
    heavy_targets = resolve_force_targets(
        spring_sizing_cfg=cfg,
        spring_count=3,
        switch_force_nominal_n=cfg.switch_force_nominal_n,
        mass_budget=heavy,
    )

    assert light_targets.mass_adjustment_delta_n == 0.0
    assert heavy_targets.mass_adjustment_delta_n > 0.0
    assert (
        heavy_targets.per_spring_force_actuation_center_n
        > light_targets.per_spring_force_actuation_center_n
    )


def test_no_candidate_status_is_reported() -> None:
    result = solve_spring(
        SpringSolveRequest(
            name="impossible",
            inputs=_solver_inputs(
                spring_sizing=SpringSizingConfig(
                    spring_count=3,
                    allowed_wire_diameters_default_mm=[0.203],
                    allowed_wire_diameters_extended_mm=[],
                    mean_diameter_candidates_mm=[5.05],
                    active_coils_min=14,
                    active_coils_max=14,
                    free_length_min_mm=0.1,
                    free_length_max_mm=0.2,
                )
            ),
        )
    )

    assert result.diagnostics.status == SPRING_SOLVER_STATUS_NO_CANDIDATES
    assert result.diagnostics.resolved is None
    assert result.diagnostics.reject_reason_histogram


def test_invalid_geometry_raises_domain_error() -> None:
    inputs = _geometry_inputs().model_copy(update={"actuation_travel_delta_mm": 0.0})

    with pytest.raises(SpringSizingError):
        derive_search_geometry(
            geometry_inputs=inputs,
            spring_sizing_cfg=SpringSizingConfig(spring_count=3),
        )


def test_fit_near_miss_requires_support_annulus_only_rejections() -> None:
    geometry = _search_geometry()
    base_physics = CandidatePhysics(
        inner_diameter_mm=4.9,
        outer_diameter_mm=5.8,
        spring_index=6.5,
        inactive_coils=2.0,
        total_coils=10.0,
        solid_height_mm=5.0,
        solid_margin_mm=0.8,
        deflection_rest_mm=0.5,
        deflection_actuation_mm=1.0,
        deflection_compressed_hard_stop_mm=1.5,
        single_spring_force_rest_n=0.2,
        single_spring_force_actuation_n=0.4,
        single_spring_force_compressed_hard_stop_n=0.6,
        total_force_actuation_with_switch_n=2.7,
        total_force_compressed_hard_stop_with_switch_n=3.4,
        stress_rest_n_per_mm2=100.0,
        stress_actuation_n_per_mm2=200.0,
        stress_compressed_hard_stop_n_per_mm2=300.0,
    )
    fit = evaluate_candidate_fit(
        physics=base_physics,
        geometry=geometry,
        support_inner_margin_min=0.15,
        support_inner_margin_preferred=0.2,
        support_outer_margin_min=0.15,
        support_outer_margin_preferred=0.2,
        spring_index_reject_below=4.0,
        solid_margin_reject_below_mm=0.3,
        compressed_hard_stop_force_preferred_min_total_n=2.0,
        near_miss_max_delta_mm=0.45,
    )
    assert fit.near_miss_advisory

    non_support_physics = base_physics.model_copy(update={"single_spring_force_actuation_n": 0.0})
    fit_with_non_support_reject = evaluate_candidate_fit(
        physics=non_support_physics,
        geometry=geometry,
        support_inner_margin_min=0.15,
        support_inner_margin_preferred=0.2,
        support_outer_margin_min=0.15,
        support_outer_margin_preferred=0.2,
        spring_index_reject_below=4.0,
        solid_margin_reject_below_mm=0.3,
        compressed_hard_stop_force_preferred_min_total_n=2.0,
        near_miss_max_delta_mm=0.45,
    )
    assert SPRING_REJECT_FORCE_ACTUATION_NON_POSITIVE in fit_with_non_support_reject.reject_reasons
    assert not fit_with_non_support_reject.near_miss_advisory


def test_score_candidate_applies_deterministic_penalties_and_warnings() -> None:
    physics = CandidatePhysics(
        inner_diameter_mm=4.5,
        outer_diameter_mm=5.8,
        spring_index=5.5,
        inactive_coils=2.0,
        total_coils=10.0,
        solid_height_mm=5.0,
        solid_margin_mm=0.3,
        deflection_rest_mm=0.2,
        deflection_actuation_mm=0.6,
        deflection_compressed_hard_stop_mm=1.0,
        single_spring_force_rest_n=0.1,
        single_spring_force_actuation_n=0.3,
        single_spring_force_compressed_hard_stop_n=0.5,
        total_force_actuation_with_switch_n=2.5,
        total_force_compressed_hard_stop_with_switch_n=3.8,
        stress_rest_n_per_mm2=100.0,
        stress_actuation_n_per_mm2=200.0,
        stress_compressed_hard_stop_n_per_mm2=1000.0,
    )
    fit = CandidateFit(
        support_inner_margin_radial_mm=0.15,
        support_outer_margin_radial_mm=0.18,
        preferred_fit_pass=False,
        near_miss_advisory=False,
        reject_reasons=[],
    )
    targets = SpringForceTargets(
        total_force_actuation_n=ForceBand(preferred_min=1.8, preferred_max=2.2, center=2.0),
        total_force_compressed_hard_stop_n=ForceBand(preferred_min=3.0, preferred_max=3.6, center=3.3),
        per_spring_force_actuation_center_n=0.0,
        per_spring_force_compressed_hard_stop_center_n=0.0,
        mass_adjustment_delta_n=0.0,
    )
    score = score_candidate(
        physics=physics,
        fit=fit,
        targets=targets,
        spring_sizing_cfg=SpringSizingConfig(score_weights=ScoreWeights()),
        wire_diameter_mm=0.35,
        active_coils=12,
        exploratory_wires={0.2, 0.35},
        spring_index_preferred_min=6.0,
        spring_index_soft_warn_above=16.0,
        solid_margin_preferred_min_mm=0.5,
        support_inner_margin_preferred=0.2,
        support_outer_margin_preferred=0.2,
        stress_soft_warn_above_n_per_mm2=900.0,
    )

    assert math.isclose(score.force_score, 0.875)
    assert math.isclose(score.candidate_score, 1.8483333333333334)
    assert score.warnings == [
        SPRING_WARN_SPRING_INDEX_OUTSIDE_PREFERRED,
        SPRING_WARN_SOLID_MARGIN_BELOW_PREFERRED,
        SPRING_WARN_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_PREFERRED,
        SPRING_WARN_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_PREFERRED,
        SPRING_WARN_EXPLORATORY_WIRE_DIAMETER,
        SPRING_WARN_STRESS_ABOVE_SOFT_WARN,
    ]
