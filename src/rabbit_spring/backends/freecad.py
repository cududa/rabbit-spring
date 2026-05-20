"""FreeCAD-backed spring model export."""

from __future__ import annotations

import importlib
import json
import math
from typing import Any

from ..constants import VISUAL_MIN_TURNS, VISUAL_RADIAL_CLEARANCE_MM
from ..errors import SpringModelExportError
from ..models.base import DomainModel
from ..models.payloads import SpringModelExportRequest, SpringModelExportResult
from ..pitch import enforce_min_pitch_for_length
from ..tokens import SPRING_MODEL_STATUS_EXPORTED, SpringEndType


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


def load_freecad_modules() -> FreeCadModules:
    try:
        return FreeCadModules(
            app_mod=importlib.import_module("FreeCAD"),
            part_mod=importlib.import_module("Part"),
            mesh_part_mod=importlib.import_module("MeshPart"),
        )
    except ImportError as exc:
        raise SpringModelExportError(
            "FreeCAD export requires FreeCAD, Part, and MeshPart to be importable"
        ) from exc


def resolve_visual_params(request: SpringModelExportRequest) -> SpringVisualParams:
    candidate = request.candidate
    installed_height_mm = request.installed_height_mm or candidate.installed_length_rest_mm
    if installed_height_mm <= 0.0:
        raise SpringModelExportError("installed spring height must be > 0")

    wire_diameter_mm = candidate.geometry.wire_diameter_mm
    mean_diameter_mm = candidate.geometry.mean_diameter_mm
    if wire_diameter_mm <= 0.0 or mean_diameter_mm <= wire_diameter_mm:
        raise SpringModelExportError("candidate has invalid wire/mean diameter geometry")

    turns = max(VISUAL_MIN_TURNS, candidate.physics.total_coils)
    turns, pitch_mm = enforce_min_pitch_for_length(
        length_mm=installed_height_mm,
        turns=turns,
        wire_diameter_mm=wire_diameter_mm,
        min_turns=1.0,
    )

    return SpringVisualParams(
        centers_xy_mm=request.centers_xy_mm,
        z0_mm=request.z0_mm,
        installed_height_mm=installed_height_mm,
        wire_diameter_mm=wire_diameter_mm,
        mean_diameter_mm=mean_diameter_mm,
        wire_radius_mm=0.5 * wire_diameter_mm,
        mean_radius_mm=0.5 * mean_diameter_mm,
        pitch_mm=pitch_mm,
        turns=turns,
        inactive_coils=max(0.0, candidate.physics.inactive_coils),
        end_type=candidate.geometry.end_type,
    )


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


def _write_stl(*, shape: Any, mesh_part_mod: Any, request: SpringModelExportRequest) -> None:
    request.output_stl.parent.mkdir(parents=True, exist_ok=True)
    mesh = mesh_part_mod.meshFromShape(
        Shape=shape,
        LinearDeflection=request.linear_deflection_mm,
        AngularDeflection=request.angular_deflection_deg,
        Relative=False,
    )
    mesh.write(str(request.output_stl))


def _write_step(*, shape: Any, part_mod: Any, request: SpringModelExportRequest) -> None:
    request.output_step.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(shape, "exportStep"):
        shape.exportStep(str(request.output_step))
        return
    if hasattr(part_mod, "export"):
        part_mod.export([shape], str(request.output_step))
        return
    raise SpringModelExportError("FreeCAD shape/Part module cannot export STEP")


def _write_report(
    *,
    request: SpringModelExportRequest,
    result: SpringModelExportResult,
) -> None:
    request.output_report.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "export": result.model_dump(mode="json"),
        "candidate": request.candidate.model_dump(mode="json"),
        "mesh": {
            "linear_deflection_mm": request.linear_deflection_mm,
            "angular_deflection_deg": request.angular_deflection_deg,
        },
    }
    request.output_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def export_spring_model(
    request: SpringModelExportRequest,
    *,
    modules: FreeCadModules | None = None,
) -> SpringModelExportResult:
    params = resolve_visual_params(request)
    freecad_modules = modules or load_freecad_modules()
    shape = build_spring_model_shape(
        app_mod=freecad_modules.app_mod,
        part_mod=freecad_modules.part_mod,
        params=params,
    )
    _write_stl(shape=shape, mesh_part_mod=freecad_modules.mesh_part_mod, request=request)
    _write_step(shape=shape, part_mod=freecad_modules.part_mod, request=request)

    result = SpringModelExportResult(
        status=SPRING_MODEL_STATUS_EXPORTED,
        backend="freecad",
        output_stl=request.output_stl,
        output_step=request.output_step,
        output_report=request.output_report,
        centers_xy_mm=params.centers_xy_mm,
        installed_height_mm=params.installed_height_mm,
        wire_diameter_mm=params.wire_diameter_mm,
        mean_diameter_mm=params.mean_diameter_mm,
        pitch_mm=params.pitch_mm,
        total_turns=params.turns,
        end_type=params.end_type,
    )
    _write_report(request=request, result=result)
    return result
