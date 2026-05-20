"""Public API functions."""

from __future__ import annotations

from .backends.freecad._export import export_spring_model as export_spring_model_freecad
from .models import (
    SpringSearchDiagnosticsPayload,
    SpringModelExportRequest,
    SpringModelExportResult,
    SpringSolveAndExportRequest,
    SpringSolveAndExportResult,
    SpringSolveRequest,
    SpringSolveResult,
)
from .solver import resolve_spring
from .tokens import SPRING_SOLVER_REASON_SIZING_NOT_CONFIGURED, SPRING_SOLVER_STATUS_NOT_REQUESTED


def solve_spring(request: SpringSolveRequest) -> SpringSolveResult:
    diagnostics = resolve_spring(name=request.name, spring_inputs=request.inputs)
    if diagnostics is None:
        diagnostics = SpringSearchDiagnosticsPayload(
            status=SPRING_SOLVER_STATUS_NOT_REQUESTED,
            name=request.name,
            reason=SPRING_SOLVER_REASON_SIZING_NOT_CONFIGURED,
        )
    return SpringSolveResult(diagnostics=diagnostics)


def export_spring_model(request: SpringModelExportRequest) -> SpringModelExportResult:
    return export_spring_model_freecad(request)


def solve_and_export(request: SpringSolveAndExportRequest) -> SpringSolveAndExportResult:
    solve_result = solve_spring(request.solve)
    active_candidate = (
        solve_result.diagnostics.resolved.active_candidate
        if solve_result.diagnostics.resolved is not None
        else None
    )
    export_result = None
    if active_candidate is not None:
        export_result = export_spring_model(
            SpringModelExportRequest(
                candidate=active_candidate,
                output_stl=request.export_output_stl,
                output_step=request.export_output_step,
                output_report=request.export_output_report,
                centers_xy_mm=request.centers_xy_mm,
                installed_height_mm=request.installed_height_mm,
            )
        )
    return SpringSolveAndExportResult(solve=solve_result, export=export_result)
