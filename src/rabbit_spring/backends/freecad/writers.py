"""FreeCAD export file writers."""

from __future__ import annotations

import json
from typing import Any

from ...errors import SpringModelExportError
from ...models.payloads import SpringModelExportRequest, SpringModelExportResult


def write_stl(*, shape: Any, mesh_part_mod: Any, request: SpringModelExportRequest) -> None:
    request.output_stl.parent.mkdir(parents=True, exist_ok=True)
    mesh = mesh_part_mod.meshFromShape(
        Shape=shape,
        LinearDeflection=request.linear_deflection_mm,
        AngularDeflection=request.angular_deflection_deg,
        Relative=False,
    )
    mesh.write(str(request.output_stl))


def write_step(*, shape: Any, part_mod: Any, request: SpringModelExportRequest) -> None:
    request.output_step.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(shape, "exportStep"):
        shape.exportStep(str(request.output_step))
        return
    if hasattr(part_mod, "export"):
        part_mod.export([shape], str(request.output_step))
        return
    raise SpringModelExportError("FreeCAD shape/Part module cannot export STEP")


def write_report(
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
