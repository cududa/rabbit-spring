"""Geometry derivation rules for spring search."""

from __future__ import annotations

from .errors import SpringSizingError
from .models.config import SpringSizingConfig
from .models.geometry import SpringGeometryInputs, SpringSearchGeometry


def derive_search_geometry(
    *,
    geometry_inputs: SpringGeometryInputs,
    spring_sizing_cfg: SpringSizingConfig,
) -> SpringSearchGeometry:
    rest_installed_default = (
        geometry_inputs.spring_top_interface_world_z_mm - geometry_inputs.well_floor_z_world_mm
    )
    if rest_installed_default <= 0.0:
        raise SpringSizingError(
            "Resolved rest installed length must be > 0 "
            f"(got {rest_installed_default:.4f})"
        )

    actuation_delta_mm = geometry_inputs.actuation_travel_delta_mm
    compressed_hard_stop_delta_mm = geometry_inputs.compressed_hard_stop_travel_delta_mm
    if actuation_delta_mm <= 0.0:
        raise SpringSizingError("actuation_travel_delta_mm must be > 0")
    if compressed_hard_stop_delta_mm <= actuation_delta_mm:
        raise SpringSizingError(
            "compressed_hard_stop_travel_delta_mm must be > actuation_travel_delta_mm"
        )

    installed_length_rest_mm = (
        spring_sizing_cfg.installed_length_rest_mm
        if spring_sizing_cfg.installed_length_rest_mm is not None
        else rest_installed_default
    )
    installed_length_actuation_mm = (
        spring_sizing_cfg.installed_length_actuation_mm
        if spring_sizing_cfg.installed_length_actuation_mm is not None
        else installed_length_rest_mm - actuation_delta_mm
    )
    installed_length_compressed_hard_stop_mm = (
        spring_sizing_cfg.installed_length_compressed_hard_stop_mm
        if spring_sizing_cfg.installed_length_compressed_hard_stop_mm is not None
        else installed_length_rest_mm - compressed_hard_stop_delta_mm
    )

    if not (
        installed_length_rest_mm
        > installed_length_actuation_mm
        > installed_length_compressed_hard_stop_mm
        > 0.0
    ):
        raise SpringSizingError(
            "Installed lengths must satisfy rest > actuation > compressed_hard_stop > 0 "
            f"(got {installed_length_rest_mm:.4f}, {installed_length_actuation_mm:.4f}, "
            f"{installed_length_compressed_hard_stop_mm:.4f})"
        )

    resolved_well_floor_z_world_mm = (
        geometry_inputs.spring_top_interface_world_z_mm - installed_length_rest_mm
    )
    return SpringSearchGeometry(
        post_outer_diameter_mm=geometry_inputs.post_outer_diameter_mm,
        support_annulus=geometry_inputs.support_annulus,
        well_inner_diameter_mm=geometry_inputs.well_inner_diameter_mm,
        spring_top_interface_world_z_mm=geometry_inputs.spring_top_interface_world_z_mm,
        well_floor_z_world_mm=resolved_well_floor_z_world_mm,
        installed_length_rest_mm=installed_length_rest_mm,
        installed_length_actuation_mm=installed_length_actuation_mm,
        installed_length_compressed_hard_stop_mm=installed_length_compressed_hard_stop_mm,
    )
