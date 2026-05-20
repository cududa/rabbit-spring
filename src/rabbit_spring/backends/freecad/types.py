"""Typed containers for the FreeCAD export backend."""

from __future__ import annotations

from typing import Any

from ...models.base import DomainModel
from ...tokens import SpringEndType


class SpringVisualParams(DomainModel):
    centers_xy_mm: list[tuple[float, float]]
    z0_mm: float
    installed_height_mm: float
    wire_diameter_mm: float
    mean_diameter_mm: float
    wire_radius_mm: float
    mean_radius_mm: float
    pitch_mm: float
    turns: float
    inactive_coils: float
    end_type: SpringEndType = "open"


class FreeCadModules(DomainModel):
    model_config = DomainModel.model_config | {"arbitrary_types_allowed": True}

    app_mod: Any
    part_mod: Any
    mesh_part_mod: Any
