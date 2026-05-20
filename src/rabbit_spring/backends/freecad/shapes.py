"""FreeCAD shape construction for spring exports."""

from __future__ import annotations

import math
from typing import Any

from ...constants import VISUAL_RADIAL_CLEARANCE_MM
from ...errors import SpringModelExportError
from .types import SpringVisualParams


def profile_normal_for_helix(
    *,
    app_mod: Any,
    pitch_mm: float,
    radius_mm: float,
) -> Any:
    if abs(radius_mm) <= 1e-9:
        return app_mod.Vector(0.0, 0.0, 1.0)
    lead_mm_per_rad = pitch_mm / (2.0 * math.pi)
    return app_mod.Vector(0.0, float(radius_mm), lead_mm_per_rad)


def _make_helix_solid(
    *,
    part_mod: Any,
    profile_wire: Any,
    pitch: float,
    height: float,
    radius: float,
) -> Any:
    helix = part_mod.makeHelix(pitch, height, radius)
    path_wire = part_mod.Wire(helix.Edges)
    return path_wire.makePipeShell([profile_wire], True, True)


def _rotate_for_phase(*, app_mod: Any, shape: Any, start_turns: float) -> None:
    phase_fraction = start_turns - math.floor(start_turns)
    if abs(phase_fraction) < 1e-9:
        return
    shape.rotate(
        app_mod.Vector(0.0, 0.0, 0.0),
        app_mod.Vector(0.0, 0.0, 1.0),
        360.0 * phase_fraction,
    )


def _clip_ground_end_faces(
    *,
    part_mod: Any,
    app_mod: Any,
    shape: Any,
    mean_radius_mm: float,
    wire_radius_mm: float,
    installed_height_mm: float,
) -> Any:
    radial_extent_mm = max(
        mean_radius_mm + wire_radius_mm + VISUAL_RADIAL_CLEARANCE_MM,
        1e-3,
    )
    half_span_mm = radial_extent_mm + max(wire_radius_mm, installed_height_mm)
    clip_box = part_mod.makeBox(
        2.0 * half_span_mm,
        2.0 * half_span_mm,
        installed_height_mm,
        app_mod.Vector(-half_span_mm, -half_span_mm, 0.0),
    )
    return shape.common(clip_box).removeSplitter()


def build_spring_helix(
    *,
    part_mod: Any,
    app_mod: Any,
    profile_wire: Any,
    params: SpringVisualParams,
) -> Any:
    wire_diameter_mm = params.wire_diameter_mm
    wire_radius_mm = params.wire_radius_mm
    mean_radius_mm = params.mean_radius_mm
    installed_height_mm = params.installed_height_mm

    def build_for_height(height_mm: float) -> Any:
        if params.end_type in ("closed", "closed_ground"):
            total_turns = params.turns
            inactive_coils = max(0.0, params.inactive_coils)
            closed_turns = 0.5 * inactive_coils
            active_turns = total_turns - inactive_coils
            closed_pitch = wire_diameter_mm
            closed_height = closed_turns * closed_pitch
            active_height = height_mm - 2.0 * closed_height

            if closed_turns <= 0.0 or active_height <= 0.0 or active_turns <= 0.0:
                spring_solid = _make_helix_solid(
                    part_mod=part_mod,
                    profile_wire=profile_wire,
                    pitch=params.pitch_mm,
                    height=height_mm,
                    radius=mean_radius_mm,
                )
                if params.end_type == "closed_ground":
                    return _clip_ground_end_faces(
                        part_mod=part_mod,
                        app_mod=app_mod,
                        shape=spring_solid,
                        mean_radius_mm=mean_radius_mm,
                        wire_radius_mm=wire_radius_mm,
                        installed_height_mm=height_mm,
                    )
                return spring_solid

            active_pitch = active_height / active_turns
            bottom_solid = _make_helix_solid(
                part_mod=part_mod,
                profile_wire=profile_wire,
                pitch=closed_pitch,
                height=closed_height,
                radius=mean_radius_mm,
            )
            mid_solid = _make_helix_solid(
                part_mod=part_mod,
                profile_wire=profile_wire,
                pitch=active_pitch,
                height=active_height,
                radius=mean_radius_mm,
            )
            _rotate_for_phase(app_mod=app_mod, shape=mid_solid, start_turns=closed_turns)
            mid_solid.translate(app_mod.Vector(0.0, 0.0, closed_height))

            top_solid = _make_helix_solid(
                part_mod=part_mod,
                profile_wire=profile_wire,
                pitch=closed_pitch,
                height=closed_height,
                radius=mean_radius_mm,
            )
            _rotate_for_phase(
                app_mod=app_mod,
                shape=top_solid,
                start_turns=closed_turns + active_turns,
            )
            top_solid.translate(app_mod.Vector(0.0, 0.0, closed_height + active_height))

            spring_solid = bottom_solid.fuse(mid_solid).fuse(top_solid).removeSplitter()
            if params.end_type == "closed_ground":
                return _clip_ground_end_faces(
                    part_mod=part_mod,
                    app_mod=app_mod,
                    shape=spring_solid,
                    mean_radius_mm=mean_radius_mm,
                    wire_radius_mm=wire_radius_mm,
                    installed_height_mm=height_mm,
                )
            return spring_solid

        return _make_helix_solid(
            part_mod=part_mod,
            profile_wire=profile_wire,
            pitch=params.pitch_mm,
            height=height_mm,
            radius=mean_radius_mm,
        )

    spring_shape = build_for_height(installed_height_mm)
    z_length_mm = spring_shape.BoundBox.ZMax - spring_shape.BoundBox.ZMin
    correction_mm = z_length_mm - installed_height_mm
    if abs(correction_mm) <= 1e-3:
        return spring_shape

    min_height_mm = max(1e-3, 0.5 * wire_diameter_mm)
    adjusted_height_mm = installed_height_mm - correction_mm
    if adjusted_height_mm <= min_height_mm:
        return spring_shape

    spring_shape = build_for_height(adjusted_height_mm)
    z_length_mm = spring_shape.BoundBox.ZMax - spring_shape.BoundBox.ZMin
    correction_mm = z_length_mm - installed_height_mm
    if abs(correction_mm) <= 1e-3:
        return spring_shape

    adjusted_height_2_mm = adjusted_height_mm - correction_mm
    if adjusted_height_2_mm <= min_height_mm:
        return spring_shape
    return build_for_height(adjusted_height_2_mm)


def build_spring_model_shape(*, app_mod: Any, part_mod: Any, params: SpringVisualParams) -> Any:
    profile_normal = profile_normal_for_helix(
        app_mod=app_mod,
        pitch_mm=params.pitch_mm,
        radius_mm=params.mean_radius_mm,
    )
    profile_wire = part_mod.Wire(
        [
            part_mod.makeCircle(
                params.wire_radius_mm,
                app_mod.Vector(float(params.mean_radius_mm), 0.0, 0.0),
                profile_normal,
            )
        ]
    )

    solids: list[Any] = []
    for center_x_mm, center_y_mm in params.centers_xy_mm:
        spring_shape = build_spring_helix(
            part_mod=part_mod,
            app_mod=app_mod,
            profile_wire=profile_wire,
            params=params,
        )
        local_z_min_mm = spring_shape.BoundBox.ZMin
        base_z_mm = params.z0_mm - local_z_min_mm
        spring_shape.translate(app_mod.Vector(float(center_x_mm), float(center_y_mm), base_z_mm))
        solids.append(spring_shape)

    if not solids:
        raise SpringModelExportError("no spring solids were generated")
    fused = solids[0]
    for solid in solids[1:]:
        fused = fused.fuse(solid)
    return fused.removeSplitter()
