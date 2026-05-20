"""Stable status, warning, and reject tokens emitted by rabbit-spring."""

from __future__ import annotations

from typing import Final, Literal, TypeAlias

SpringEndType: TypeAlias = Literal["open", "closed", "closed_ground"]

SpringSolverStatus: TypeAlias = Literal[
    "spring.solver.status.not_requested",
    "spring.solver.status.mass_budget_only",
    "spring.solver.status.computed",
    "spring.solver.status.no_strict_fit_candidates",
    "spring.solver.status.no_candidates",
]
SpringSolverReason: TypeAlias = Literal["spring.solver.reason.sizing_not_configured"]

SPRING_SOLVER_STATUS_NOT_REQUESTED: Final[SpringSolverStatus] = "spring.solver.status.not_requested"
SPRING_SOLVER_STATUS_MASS_BUDGET_ONLY: Final[SpringSolverStatus] = (
    "spring.solver.status.mass_budget_only"
)
SPRING_SOLVER_STATUS_COMPUTED: Final[SpringSolverStatus] = "spring.solver.status.computed"
SPRING_SOLVER_STATUS_NO_STRICT_FIT_CANDIDATES: Final[SpringSolverStatus] = (
    "spring.solver.status.no_strict_fit_candidates"
)
SPRING_SOLVER_STATUS_NO_CANDIDATES: Final[SpringSolverStatus] = (
    "spring.solver.status.no_candidates"
)
SPRING_SOLVER_REASON_SIZING_NOT_CONFIGURED: Final[SpringSolverReason] = (
    "spring.solver.reason.sizing_not_configured"
)

SPRING_REJECT_SPRING_INDEX_BELOW_MIN: Final[str] = "spring.search.reject.spring_index_below_min"
SPRING_REJECT_SOLID_MARGIN_BELOW_MIN: Final[str] = "spring.search.reject.solid_margin_below_min"
SPRING_REJECT_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_MIN: Final[str] = (
    "spring.search.reject.support_annulus_inner_margin_below_min"
)
SPRING_REJECT_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_MIN: Final[str] = (
    "spring.search.reject.support_annulus_outer_margin_below_min"
)
SPRING_REJECT_WELL_INNER_CLEARANCE_NON_POSITIVE: Final[str] = (
    "spring.search.reject.well_inner_clearance_non_positive"
)
SPRING_REJECT_FORCE_ACTUATION_NON_POSITIVE: Final[str] = (
    "spring.search.reject.force_actuation_non_positive"
)
SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_BELOW_PREFERRED_MIN: Final[str] = (
    "spring.search.reject.force_compressed_hard_stop_below_preferred_min"
)
SPRING_REJECT_FORCE_COMPRESSED_HARD_STOP_NOT_ABOVE_ACTUATION: Final[str] = (
    "spring.search.reject.force_compressed_hard_stop_not_above_actuation"
)
SPRING_REJECT_NEGATIVE_DEFLECTION: Final[str] = "spring.search.reject.negative_deflection"
SPRING_REJECT_INVALID_DIAMETER_GEOMETRY: Final[str] = (
    "spring.search.reject.invalid_diameter_geometry"
)
SPRING_REJECT_INVALID_SPRING_RATE: Final[str] = "spring.search.reject.invalid_spring_rate"
SPRING_REJECT_FREE_LENGTH_OUTSIDE_BAND: Final[str] = (
    "spring.search.reject.free_length_outside_band"
)
SPRING_REJECT_SUPPORT_ANNULUS_ONLY_REASONS: Final[frozenset[str]] = frozenset(
    {
        SPRING_REJECT_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_MIN,
        SPRING_REJECT_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_MIN,
        SPRING_REJECT_WELL_INNER_CLEARANCE_NON_POSITIVE,
    }
)

SPRING_WARN_SPRING_INDEX_OUTSIDE_PREFERRED: Final[str] = (
    "spring.search.warn.spring_index_outside_preferred"
)
SPRING_WARN_SOLID_MARGIN_BELOW_PREFERRED: Final[str] = (
    "spring.search.warn.solid_margin_below_preferred"
)
SPRING_WARN_SUPPORT_ANNULUS_INNER_MARGIN_BELOW_PREFERRED: Final[str] = (
    "spring.search.warn.support_annulus_inner_margin_below_preferred"
)
SPRING_WARN_SUPPORT_ANNULUS_OUTER_MARGIN_BELOW_PREFERRED: Final[str] = (
    "spring.search.warn.support_annulus_outer_margin_below_preferred"
)
SPRING_WARN_EXPLORATORY_WIRE_DIAMETER: Final[str] = (
    "spring.search.warn.exploratory_wire_diameter"
)
SPRING_WARN_VERY_LOW_ACTIVE_COILS: Final[str] = "spring.search.warn.very_low_active_coils"
SPRING_WARN_STRESS_ABOVE_SOFT_WARN: Final[str] = "spring.search.warn.stress_above_soft_warn"

SPRING_MODEL_STATUS_EXPORTED: Final[str] = "spring.model.status.exported"
SPRING_MODEL_STATUS_FAILED: Final[str] = "spring.model.status.failed"


def histogram_add(histogram: dict[str, int], reason: str) -> None:
    histogram[reason] = histogram.get(reason, 0) + 1
