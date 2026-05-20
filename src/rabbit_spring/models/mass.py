"""Mass budget result models."""

from __future__ import annotations

from .base import DomainModel
from .config import SpringMassSource


class GeometryItemResult(DomainModel):
    name: str
    source: SpringMassSource
    volume_mm3: float
    density_g_cm3: float
    scale: float
    mass_g: float


class FixedItemResult(DomainModel):
    name: str
    mass_g: float


class MassBudgetResult(DomainModel):
    geometry_items: list[GeometryItemResult]
    fixed_items: list[FixedItemResult]
    geometry_mass_g: float
    fixed_mass_g: float
    total_mass_g: float
    gravity_load_n: float
    gravity_safety_factor: float
    gravity_margin_n: float
    gravity_design_force_n: float
