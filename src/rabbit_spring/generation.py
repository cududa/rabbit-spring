"""Candidate generation loop for spring search."""

from __future__ import annotations

from .fit import evaluate_candidate_fit
from .models import (
    CandidateGeometry,
    DomainModel,
    SpringCandidate,
    SpringForceTargets,
    SpringSearchGeometry,
    SpringSizingConfig,
)
from .physics import compute_candidate_physics
from .score import score_candidate
from .tokens import (
    SPRING_REJECT_FREE_LENGTH_OUTSIDE_BAND,
    SPRING_REJECT_INVALID_DIAMETER_GEOMETRY,
    SPRING_REJECT_INVALID_SPRING_RATE,
    SpringEndType,
    histogram_add,
)


class SearchResult(DomainModel):
    ranked_candidates: list[SpringCandidate]
    near_miss_candidates: list[SpringCandidate]
    reject_reason_histogram: dict[str, int]


def _candidate_id(
    *, wire_diameter_mm: float, mean_diameter_mm: float, active_coils: int, end_type: SpringEndType
) -> str:
    return f"d{wire_diameter_mm:.2f}_D{mean_diameter_mm:.2f}_Na{active_coils}_{end_type}"


def _build_candidate(
    *,
    spring_count: int,
    spring_sizing_cfg: SpringSizingConfig,
    wire_diameter_mm: float,
    mean_diameter_mm: float,
    active_coils: int,
    end_type: SpringEndType,
    free_length_mm: float,
    spring_rate_n_per_mm: float,
    geometry: SpringSearchGeometry,
    force_targets: SpringForceTargets,
    exploratory_wires: set[float],
) -> tuple[SpringCandidate, list[str]]:
    physics = compute_candidate_physics(
        spring_count=spring_count,
        wire_diameter_mm=wire_diameter_mm,
        mean_diameter_mm=mean_diameter_mm,
        active_coils=active_coils,
        end_type=end_type,
        free_length_mm=free_length_mm,
        spring_rate_n_per_mm=spring_rate_n_per_mm,
        geometry=geometry,
        switch_force_nominal_n=spring_sizing_cfg.switch_force_nominal_n,
    )

    fit = evaluate_candidate_fit(
        physics=physics,
        geometry=geometry,
        support_inner_margin_min=spring_sizing_cfg.support_annulus_inner_margin_min_radial_mm,
        support_inner_margin_preferred=(
            spring_sizing_cfg.support_annulus_inner_margin_preferred_radial_mm
        ),
        support_outer_margin_min=spring_sizing_cfg.support_annulus_outer_margin_min_radial_mm,
        support_outer_margin_preferred=(
            spring_sizing_cfg.support_annulus_outer_margin_preferred_radial_mm
        ),
        spring_index_reject_below=spring_sizing_cfg.spring_index_reject_below,
        solid_margin_reject_below_mm=spring_sizing_cfg.solid_margin_reject_below_mm,
        compressed_hard_stop_force_preferred_min_total_n=(
            force_targets.total_force_compressed_hard_stop_n.preferred_min
        ),
        near_miss_max_delta_mm=spring_sizing_cfg.near_miss_max_delta_mm,
    )

    scoring = score_candidate(
        physics=physics,
        fit=fit,
        targets=force_targets,
        spring_sizing_cfg=spring_sizing_cfg,
        wire_diameter_mm=wire_diameter_mm,
        active_coils=active_coils,
        exploratory_wires=exploratory_wires,
        spring_index_preferred_min=spring_sizing_cfg.spring_index_preferred_min,
        spring_index_soft_warn_above=spring_sizing_cfg.spring_index_soft_warn_above,
        solid_margin_preferred_min_mm=spring_sizing_cfg.solid_margin_preferred_min_mm,
        support_inner_margin_preferred=(
            spring_sizing_cfg.support_annulus_inner_margin_preferred_radial_mm
        ),
        support_outer_margin_preferred=(
            spring_sizing_cfg.support_annulus_outer_margin_preferred_radial_mm
        ),
        stress_soft_warn_above_n_per_mm2=spring_sizing_cfg.stress_soft_warn_above_n_per_mm2,
    )

    candidate = SpringCandidate(
        candidate_id=_candidate_id(
            wire_diameter_mm=wire_diameter_mm,
            mean_diameter_mm=mean_diameter_mm,
            active_coils=active_coils,
            end_type=end_type,
        ),
        geometry=CandidateGeometry(
            wire_diameter_mm=wire_diameter_mm,
            mean_diameter_mm=mean_diameter_mm,
            active_coils=active_coils,
            free_length_mm=free_length_mm,
            spring_rate_n_per_mm=spring_rate_n_per_mm,
            end_type=end_type,
        ),
        physics=physics,
        fit=fit,
        score=scoring,
    )
    return candidate, fit.reject_reasons


def run_search(
    *,
    spring_count: int,
    spring_sizing_cfg: SpringSizingConfig,
    geometry: SpringSearchGeometry,
    force_targets: SpringForceTargets,
    wire_diameters_mm: list[float],
) -> SearchResult:
    ranked_candidates: list[SpringCandidate] = []
    near_miss_candidates: list[SpringCandidate] = []
    reject_reason_histogram: dict[str, int] = {}

    exploratory_wires = set(spring_sizing_cfg.allowed_wire_diameters_extended_mm)
    end_styles: list[SpringEndType] = (
        spring_sizing_cfg.end_styles
        if spring_sizing_cfg.end_styles
        else [spring_sizing_cfg.end_style_default]
    )

    for wire_diameter_mm in wire_diameters_mm:
        for mean_diameter_mm in spring_sizing_cfg.mean_diameter_candidates_mm:
            for active_coils in range(
                spring_sizing_cfg.active_coils_min,
                spring_sizing_cfg.active_coils_max + 1,
            ):
                if mean_diameter_mm <= wire_diameter_mm:
                    histogram_add(reject_reason_histogram, SPRING_REJECT_INVALID_DIAMETER_GEOMETRY)
                    continue

                spring_rate_n_per_mm = (
                    spring_sizing_cfg.shear_modulus_n_per_mm2 * (wire_diameter_mm**4)
                ) / max(8.0 * (mean_diameter_mm**3) * active_coils, 1e-9)
                if spring_rate_n_per_mm <= 0:
                    histogram_add(reject_reason_histogram, SPRING_REJECT_INVALID_SPRING_RATE)
                    continue

                target_deflection_actuation_mm = (
                    force_targets.per_spring_force_actuation_center_n / spring_rate_n_per_mm
                )
                free_length_mm = geometry.installed_length_actuation_mm + target_deflection_actuation_mm
                if (
                    free_length_mm < spring_sizing_cfg.free_length_min_mm
                    or free_length_mm > spring_sizing_cfg.free_length_max_mm
                ):
                    histogram_add(reject_reason_histogram, SPRING_REJECT_FREE_LENGTH_OUTSIDE_BAND)
                    continue

                for end_type in end_styles:
                    candidate, reject_reasons = _build_candidate(
                        spring_count=spring_count,
                        spring_sizing_cfg=spring_sizing_cfg,
                        wire_diameter_mm=wire_diameter_mm,
                        mean_diameter_mm=mean_diameter_mm,
                        active_coils=active_coils,
                        end_type=end_type,
                        free_length_mm=free_length_mm,
                        spring_rate_n_per_mm=spring_rate_n_per_mm,
                        geometry=geometry,
                        force_targets=force_targets,
                        exploratory_wires=exploratory_wires,
                    )
                    for reason in reject_reasons:
                        histogram_add(reject_reason_histogram, reason)
                    if len(reject_reasons) == 0:
                        ranked_candidates.append(candidate)
                    elif candidate.fit.near_miss_advisory:
                        near_miss_candidates.append(candidate)

    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda item: (item.score.candidate_score, item.score.force_score, item.geometry.active_coils),
    )
    near_miss_candidates = sorted(
        near_miss_candidates,
        key=lambda item: (item.score.candidate_score, item.score.force_score, item.geometry.active_coils),
    )
    return SearchResult(
        ranked_candidates=ranked_candidates,
        near_miss_candidates=near_miss_candidates,
        reject_reason_histogram=reject_reason_histogram,
    )
