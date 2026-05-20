"""Candidate fit and reject-rule evaluation."""

from __future__ import annotations

from .models.candidates import CandidateFit, CandidatePhysics
from .models.geometry import SpringSearchGeometry
from .tokens import (
    SPRING_REJECT_FORCE_ACTUATION_NON_POSITIVE,
    SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_BELOW_PREFERRED_MIN,
    SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_NOT_ABOVE_ACTUATION,
    SPRING_REJECT_NEGATIVE_DEFLECTION,
    SPRING_REJECT_SOLID_MARGIN_BELOW_MIN,
    SPRING_REJECT_SPRING_INDEX_BELOW_MIN,
    SPRING_REJECT_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_MIN,
    SPRING_REJECT_SUPPORT_ANNULUS_ONLY_REASONS,
    SPRING_REJECT_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_MIN,
    SPRING_REJECT_WELL_INNER_CLEARANCE_NON_POSITIVE,
)


def evaluate_candidate_fit(
    *,
    physics: CandidatePhysics,
    geometry: SpringSearchGeometry,
    support_inner_margin_min: float,
    support_inner_margin_preferred: float,
    support_outer_margin_min: float,
    support_outer_margin_preferred: float,
    spring_index_reject_below: float,
    solid_margin_reject_below_mm: float,
    compressed_hard_stop_force_preferred_min_total_n: float,
    near_miss_max_delta_mm: float,
) -> CandidateFit:
    support_inner_margin_radial_mm = 0.5 * (
        physics.inner_diameter_mm - geometry.support_annulus.inner_diameter_mm
    )
    support_outer_margin_radial_mm = 0.5 * (
        geometry.support_annulus.outer_diameter_mm - physics.outer_diameter_mm
    )
    well_clearance_radial_mm = 0.5 * (geometry.well_inner_diameter_mm - physics.outer_diameter_mm)

    required_support_inner_diameter_mm = (
        physics.inner_diameter_mm - (2.0 * support_inner_margin_preferred)
    )
    required_support_outer_diameter_mm = (
        physics.outer_diameter_mm + (2.0 * support_outer_margin_preferred)
    )
    required_support_inner_delta_mm = (
        required_support_inner_diameter_mm - geometry.support_annulus.inner_diameter_mm
    )
    required_support_outer_delta_mm = (
        required_support_outer_diameter_mm - geometry.support_annulus.outer_diameter_mm
    )
    required_well_id_delta_mm = max(0.0, physics.outer_diameter_mm - geometry.well_inner_diameter_mm)

    preferred_fit_pass = (
        support_inner_margin_radial_mm >= support_inner_margin_preferred
        and support_outer_margin_radial_mm >= support_outer_margin_preferred
    )

    reject_reasons: list[str] = []
    if physics.spring_index < spring_index_reject_below:
        reject_reasons.append(SPRING_REJECT_SPRING_INDEX_BELOW_MIN)
    if physics.solid_margin_mm < solid_margin_reject_below_mm:
        reject_reasons.append(SPRING_REJECT_SOLID_MARGIN_BELOW_MIN)
    if support_inner_margin_radial_mm < support_inner_margin_min:
        reject_reasons.append(SPRING_REJECT_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_MIN)
    if support_outer_margin_radial_mm < support_outer_margin_min:
        reject_reasons.append(SPRING_REJECT_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_MIN)
    if well_clearance_radial_mm <= 0.0:
        reject_reasons.append(SPRING_REJECT_WELL_INNER_CLEARANCE_NON_POSITIVE)
    if physics.single_spring_force_actuation_n <= 0.0:
        reject_reasons.append(SPRING_REJECT_FORCE_ACTUATION_NON_POSITIVE)
    if (
        physics.total_force_compressed_hard_stop_with_switch_n
        < compressed_hard_stop_force_preferred_min_total_n
    ):
        reject_reasons.append(SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_BELOW_PREFERRED_MIN)
    if physics.single_spring_force_compressed_hard_stop_n <= physics.single_spring_force_actuation_n:
        reject_reasons.append(SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_NOT_ABOVE_ACTUATION)
    if (
        physics.deflection_rest_mm < 0.0
        or physics.deflection_actuation_mm < 0.0
        or physics.deflection_compressed_hard_stop_mm < 0.0
    ):
        reject_reasons.append(SPRING_REJECT_NEGATIVE_DEFLECTION)

    support_annulus_related_only = bool(reject_reasons) and all(
        reason in SPRING_REJECT_SUPPORT_ANNULUS_ONLY_REASONS for reason in reject_reasons
    )
    near_miss_advisory = (
        support_annulus_related_only
        and max(
            abs(required_support_inner_delta_mm),
            abs(required_support_outer_delta_mm),
            abs(required_well_id_delta_mm),
        )
        <= near_miss_max_delta_mm
    )

    return CandidateFit(
        support_inner_margin_radial_mm=support_inner_margin_radial_mm,
        support_outer_margin_radial_mm=support_outer_margin_radial_mm,
        preferred_fit_pass=preferred_fit_pass,
        near_miss_advisory=near_miss_advisory,
        reject_reasons=reject_reasons,
    )
