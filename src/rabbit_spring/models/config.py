"""Spring solver configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from ..tokens import SpringEndType
from .base import DomainModel


def _default_wire_diameters_mm() -> list[float]:
    return [0.203, 0.229, 0.254, 0.279, 0.305, 0.330, 0.356, 0.381, 0.406]


def _empty_float_list() -> list[float]:
    return []


def _default_mean_diameters_mm() -> list[float]:
    return [5.05, 5.10, 5.15, 5.20, 5.25]


def _default_end_styles() -> list[SpringEndType]:
    return ["closed_ground"]


class ForceBand(DomainModel):
    preferred_min: float
    preferred_max: float
    center: float

    @model_validator(mode="after")
    def _validate_bounds(self) -> "ForceBand":
        if self.preferred_min <= 0.0:
            raise ValueError("preferred_min must be > 0")
        if self.preferred_max < self.preferred_min:
            raise ValueError("preferred_max must be >= preferred_min")
        if self.center < self.preferred_min or self.center > self.preferred_max:
            raise ValueError("center must be within [preferred_min, preferred_max]")
        return self

    def with_shift(self, shift: float) -> "ForceBand":
        return ForceBand(
            preferred_min=float(self.preferred_min + shift),
            preferred_max=float(self.preferred_max + shift),
            center=float(self.center + shift),
        )


class ScoreWeights(DomainModel):
    actuation_error: float = 1.00
    compressed_hard_stop_error: float = 0.75
    solid_margin: float = 2.0
    fit_margin: float = 2.0
    stress: float = 1.0
    simplicity: float = 0.05


class SpringSizingConfig(DomainModel):
    spring_count: int = 3
    switch_force_nominal_n: float = 1.57
    shear_modulus_n_per_mm2: float = 79300.0
    end_style_default: SpringEndType = "closed_ground"
    end_styles: list[SpringEndType] = Field(default_factory=_default_end_styles)
    installed_length_rest_mm: float | None = None
    installed_length_actuation_mm: float | None = None
    installed_length_compressed_hard_stop_mm: float | None = None
    allowed_wire_diameters_default_mm: list[float] = Field(
        default_factory=_default_wire_diameters_mm,
    )
    allowed_wire_diameters_extended_mm: list[float] = Field(default_factory=_empty_float_list)
    mean_diameter_candidates_mm: list[float] = Field(default_factory=_default_mean_diameters_mm)
    active_coils_min: int = 2
    active_coils_max: int = 14
    free_length_min_mm: float = 4.0
    free_length_max_mm: float = 12.0
    spring_index_reject_below: float = 4.0
    spring_index_preferred_min: float = 6.0
    spring_index_soft_warn_above: float = 16.0
    solid_margin_reject_below_mm: float = 0.30
    solid_margin_preferred_min_mm: float = 0.50
    support_annulus_inner_margin_min_radial_mm: float = 0.15
    support_annulus_inner_margin_preferred_radial_mm: float = 0.20
    support_annulus_outer_margin_min_radial_mm: float = 0.15
    support_annulus_outer_margin_preferred_radial_mm: float = 0.20
    stress_soft_warn_above_n_per_mm2: float = 900.0
    near_miss_max_delta_mm: float = 0.35
    target_total_force_actuation_n: ForceBand = Field(
        default_factory=lambda: ForceBand(preferred_min=2.20, preferred_max=2.40, center=2.30),
    )
    target_total_force_compressed_hard_stop_n: ForceBand = Field(
        default_factory=lambda: ForceBand(preferred_min=2.50, preferred_max=2.85, center=2.65),
    )
    score_weights: ScoreWeights = Field(default_factory=ScoreWeights)
    diagnostics_top_k: int = 5

    @field_validator("end_style_default", mode="before")
    @classmethod
    def _normalize_end_style_default(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("end_styles", mode="before")
    @classmethod
    def _normalize_end_styles(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value]

    @model_validator(mode="after")
    def _validate_ranges(self) -> "SpringSizingConfig":
        if self.spring_count < 1:
            raise ValueError("spring_count must be >= 1")
        if self.active_coils_max < self.active_coils_min:
            raise ValueError("active_coils_max must be >= active_coils_min")
        if self.free_length_max_mm < self.free_length_min_mm:
            raise ValueError("free_length_max_mm must be >= free_length_min_mm")
        if self.diagnostics_top_k < 0:
            raise ValueError("diagnostics_top_k must be >= 0")
        return self


SpringMassSource = Literal["cap_volume_mm3"]


def _default_geometry_items() -> list["MassBudgetGeometryItemConfig"]:
    return [MassBudgetGeometryItemConfig()]


def _empty_fixed_items() -> list["MassBudgetFixedItemConfig"]:
    return []


class MassBudgetGeometryItemConfig(DomainModel):
    name: str = "cap"
    source: SpringMassSource = "cap_volume_mm3"
    density_g_cm3: float = 1.10
    scale: float = 1.0


class MassBudgetFixedItemConfig(DomainModel):
    name: str
    mass_g: float = 0.0


class MassBudgetConfig(DomainModel):
    geometry_items: list[MassBudgetGeometryItemConfig] = Field(
        default_factory=_default_geometry_items,
    )
    fixed_items: list[MassBudgetFixedItemConfig] = Field(default_factory=_empty_fixed_items)
    gravity_safety_factor: float = 1.20
    gravity_margin_n: float = 0.05
