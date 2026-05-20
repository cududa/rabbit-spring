"""Geometry input and derived search envelope models."""

from __future__ import annotations

from pydantic import computed_field, model_validator

from .base import DomainModel


class SpringSupportAnnulus(DomainModel):
    inner_diameter_mm: float
    outer_diameter_mm: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def radial_width_mm(self) -> float:
        return 0.5 * (self.outer_diameter_mm - self.inner_diameter_mm)

    @model_validator(mode="after")
    def _validate_support_annulus(self) -> "SpringSupportAnnulus":
        if self.inner_diameter_mm <= 0.0:
            raise ValueError("support annulus inner diameter must be > 0")
        if self.outer_diameter_mm <= self.inner_diameter_mm:
            raise ValueError("support annulus outer diameter must be > inner diameter")
        return self


class SpringGeometryInputs(DomainModel):
    spring_count: int
    post_outer_diameter_mm: float
    support_annulus: SpringSupportAnnulus
    well_inner_diameter_mm: float
    spring_top_interface_world_z_mm: float
    well_floor_z_world_mm: float
    actuation_travel_delta_mm: float
    compressed_hard_stop_travel_delta_mm: float


class SpringSearchGeometry(DomainModel):
    post_outer_diameter_mm: float
    support_annulus: SpringSupportAnnulus
    well_inner_diameter_mm: float
    spring_top_interface_world_z_mm: float
    well_floor_z_world_mm: float
    installed_length_rest_mm: float
    installed_length_actuation_mm: float
    installed_length_compressed_hard_stop_mm: float
