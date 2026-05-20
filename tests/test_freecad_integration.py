from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from rabbit_spring import SpringModelExportRequest, SpringSolveRequest, export_spring_model, solve_spring
from tests.test_solver import make_solver_inputs


freecad_available = (
    importlib.util.find_spec("FreeCAD") is not None
    and importlib.util.find_spec("Part") is not None
    and importlib.util.find_spec("MeshPart") is not None
)


@pytest.mark.freecad
@pytest.mark.skipif(not freecad_available, reason="FreeCAD modules are not importable")
def test_real_freecad_export_writes_artifacts(tmp_path: Path) -> None:
    result = solve_spring(SpringSolveRequest(name="integration", inputs=make_solver_inputs()))
    assert result.diagnostics.resolved is not None

    export = export_spring_model(
        SpringModelExportRequest(
            candidate=result.diagnostics.resolved.active_candidate,
            output_stl=tmp_path / "spring.stl",
            output_step=tmp_path / "spring.step",
            output_report=tmp_path / "spring.json",
        )
    )

    assert export.output_stl.exists()
    assert export.output_step.exists()
    assert export.output_report.exists()
