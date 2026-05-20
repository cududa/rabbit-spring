"""FreeCAD export orchestration."""

from __future__ import annotations

from ...models.payloads import SpringModelExportRequest, SpringModelExportResult
from ...tokens import SPRING_MODEL_STATUS_EXPORTED
from .loader import load_freecad_modules
from .shapes import build_spring_model_shape
from .types import FreeCadModules
from .visual import resolve_visual_params
from .writers import write_report, write_step, write_stl


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
    write_stl(shape=shape, mesh_part_mod=freecad_modules.mesh_part_mod, request=request)
    write_step(shape=shape, part_mod=freecad_modules.part_mod, request=request)

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
    write_report(request=request, result=result)
    return result
