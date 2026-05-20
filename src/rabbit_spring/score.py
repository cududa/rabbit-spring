"""Candidate scoring logic."""

from __future__ import annotations

from .models import CandidateFit, CandidatePhysics, CandidateScore, SpringForceTargets, SpringSizingConfig
from .tokens import (
    SPRING_WARN_EXPLORATORY_WIRE_DIAMETER,
    SPRING_WARN_SOLID_MARGIN_BELOW_PREFERRED,
    SPRING_WARN_SPRING_INDEX_OUTSIDE_PREFERRED,
    SPRING_WARN_STRESS_ABOVE_SOFT_WARN,
    SPRING_WARN_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_PREFERRED,
    SPRING_WARN_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_PREFERRED,
    SPRING_WARN_VERY_LOW_ACTIVE_COILS,
)


def score_candidate(
    *,
    physics: CandidatePhysics,
    fit: CandidateFit,
    targets: SpringForceTargets,
    spring_sizing_cfg: SpringSizingConfig,
    wire_diameter_mm: float,
    active_coils: int,
    exploratory_wires: set[float],
    spring_index_preferred_min: float,
    spring_index_soft_warn_above: float,
    solid_margin_preferred_min_mm: float,
    support_inner_margin_preferred: float,
    support_outer_margin_preferred: float,
    stress_soft_warn_above_n_per_mm2: float,
) -> CandidateScore:
    weights = spring_sizing_cfg.score_weights

    candidate_force_score = (
        weights.actuation_error
        * abs(physics.total_force_actuation_with_switch_n - targets.total_force_actuation_n.center)
        + weights.compressed_hard_stop_error
        * abs(
            physics.total_force_compressed_hard_stop_with_switch_n
            - targets.total_force_compressed_hard_stop_n.center
        )
    )

    solid_penalty = (
        0.0
        if physics.solid_margin_mm >= solid_margin_preferred_min_mm
        else (solid_margin_preferred_min_mm - physics.solid_margin_mm) * weights.solid_margin
    )
    fit_penalty = 0.0
    if fit.support_inner_margin_radial_mm < support_inner_margin_preferred:
        fit_penalty += (
            support_inner_margin_preferred - fit.support_inner_margin_radial_mm
        ) * weights.fit_margin
    if fit.support_outer_margin_radial_mm < support_outer_margin_preferred:
        fit_penalty += (
            support_outer_margin_preferred - fit.support_outer_margin_radial_mm
        ) * weights.fit_margin
    stress_penalty = 0.0
    if physics.stress_compressed_hard_stop_n_per_mm2 > stress_soft_warn_above_n_per_mm2:
        stress_penalty += (
            (physics.stress_compressed_hard_stop_n_per_mm2 - stress_soft_warn_above_n_per_mm2)
            / 300.0
        ) * weights.stress
    simplicity_penalty = 0.0 if active_coils <= 10 else (active_coils - 10) * weights.simplicity

    candidate_score = (
        candidate_force_score + solid_penalty + fit_penalty + stress_penalty + simplicity_penalty
    )

    warnings: list[str] = []
    if (
        physics.spring_index < spring_index_preferred_min
        or physics.spring_index > spring_index_soft_warn_above
    ):
        warnings.append(SPRING_WARN_SPRING_INDEX_OUTSIDE_PREFERRED)
    if physics.solid_margin_mm < solid_margin_preferred_min_mm:
        warnings.append(SPRING_WARN_SOLID_MARGIN_BELOW_PREFERRED)
    if fit.support_inner_margin_radial_mm < support_inner_margin_preferred:
        warnings.append(SPRING_WARN_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_PREFERRED)
    if fit.support_outer_margin_radial_mm < support_outer_margin_preferred:
        warnings.append(SPRING_WARN_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_PREFERRED)
    if any(abs(wire_diameter_mm - exploratory_wire) <= 1e-9 for exploratory_wire in exploratory_wires):
        warnings.append(SPRING_WARN_EXPLORATORY_WIRE_DIAMETER)
    if active_coils <= 3:
        warnings.append(SPRING_WARN_VERY_LOW_ACTIVE_COILS)
    if physics.stress_compressed_hard_stop_n_per_mm2 > stress_soft_warn_above_n_per_mm2:
        warnings.append(SPRING_WARN_STRESS_ABOVE_SOFT_WARN)

    notes: list[str] = []
    if fit.near_miss_advisory:
        notes.append("near miss: candidate can be unlocked with small support-annulus geometry changes")
    if fit.preferred_fit_pass and physics.solid_margin_mm >= solid_margin_preferred_min_mm:
        notes.append("good balanced candidate")
    if active_coils <= 4:
        notes.append("simple low-coil candidate")

    return CandidateScore(
        candidate_score=candidate_score,
        force_score=candidate_force_score,
        warnings=warnings,
        notes=notes,
    )
