"""Force-target derivation rules for spring search."""

from __future__ import annotations

from .models.config import SpringSizingConfig
from .models.mass import MassBudgetResult
from .models.payloads import SpringForceTargets


def resolve_force_targets(
    *,
    spring_sizing_cfg: SpringSizingConfig,
    spring_count: int,
    switch_force_nominal_n: float,
    mass_budget: MassBudgetResult,
) -> SpringForceTargets:
    actuation_band = spring_sizing_cfg.target_total_force_actuation_n
    hard_stop_band = spring_sizing_cfg.target_total_force_compressed_hard_stop_n

    mass_floor_total_n = mass_budget.gravity_design_force_n
    mass_adjustment_delta_n = max(0.0, mass_floor_total_n - actuation_band.center)
    adjusted_actuation = actuation_band.with_shift(mass_adjustment_delta_n)
    adjusted_hard_stop = hard_stop_band.with_shift(mass_adjustment_delta_n)
    if adjusted_hard_stop.center <= adjusted_actuation.center:
        adjustment = (adjusted_actuation.center + 0.10) - adjusted_hard_stop.center
        adjusted_hard_stop = adjusted_hard_stop.with_shift(adjustment)

    per_spring_force_actuation_center_n = max(
        0.0,
        adjusted_actuation.center / float(spring_count),
    )
    per_spring_force_compressed_hard_stop_center_n = max(
        0.0,
        (adjusted_hard_stop.center - switch_force_nominal_n) / float(spring_count),
    )

    return SpringForceTargets(
        total_force_actuation_n=adjusted_actuation,
        total_force_compressed_hard_stop_n=adjusted_hard_stop,
        per_spring_force_actuation_center_n=per_spring_force_actuation_center_n,
        per_spring_force_compressed_hard_stop_center_n=per_spring_force_compressed_hard_stop_center_n,
        mass_adjustment_delta_n=mass_adjustment_delta_n,
    )
