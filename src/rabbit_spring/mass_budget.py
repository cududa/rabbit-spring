"""Mass-budget calculations used to compensate spring force targets."""

from __future__ import annotations

from .constants import GRAVITY_M_S2
from .models import (
    FixedItemResult,
    GeometryItemResult,
    MassBudgetConfig,
    MassBudgetResult,
)


def compute_mass_budget(
    *,
    mass_budget_cfg: MassBudgetConfig | None,
    cap_volume_mm3: float,
) -> MassBudgetResult:
    cfg = mass_budget_cfg if mass_budget_cfg is not None else MassBudgetConfig()

    geometry_items: list[GeometryItemResult] = []
    geometry_mass_g = 0.0
    for item in cfg.geometry_items:
        volume_mm3 = cap_volume_mm3
        mass_g = (volume_mm3 / 1000.0) * item.density_g_cm3 * item.scale
        geometry_mass_g += mass_g
        geometry_items.append(
            GeometryItemResult(
                name=item.name,
                source=item.source,
                volume_mm3=volume_mm3,
                density_g_cm3=item.density_g_cm3,
                scale=item.scale,
                mass_g=mass_g,
            )
        )

    fixed_items: list[FixedItemResult] = []
    fixed_mass_g = 0.0
    for item in cfg.fixed_items:
        fixed_mass_g += item.mass_g
        fixed_items.append(FixedItemResult(name=item.name, mass_g=item.mass_g))

    total_mass_g = geometry_mass_g + fixed_mass_g
    gravity_load_n = (total_mass_g / 1000.0) * GRAVITY_M_S2
    gravity_design_force_n = gravity_load_n * cfg.gravity_safety_factor + cfg.gravity_margin_n

    return MassBudgetResult(
        geometry_items=geometry_items,
        fixed_items=fixed_items,
        geometry_mass_g=geometry_mass_g,
        fixed_mass_g=fixed_mass_g,
        total_mass_g=total_mass_g,
        gravity_load_n=gravity_load_n,
        gravity_safety_factor=cfg.gravity_safety_factor,
        gravity_margin_n=cfg.gravity_margin_n,
        gravity_design_force_n=gravity_design_force_n,
    )
