from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

from pytest import MonkeyPatch

from rabbit_spring import export_spring_model, solve_spring
from rabbit_spring.models import SpringModelExportRequest, SpringSolveRequest
from tests.helpers import make_solver_inputs


class FakeBoundBox:
    def __init__(self, z_min: float = 0.0, z_max: float = 6.0) -> None:
        self.ZMin = z_min
        self.ZMax = z_max


class FakeShape:
    def __init__(self, part: "FakePart", z_min: float = 0.0, z_max: float = 6.0) -> None:
        self.part = part
        self.BoundBox = FakeBoundBox(z_min, z_max)
        self.translate_calls: list[tuple[float, float, float]] = []
        self.rotate_calls: list[float] = []
        self.common_calls = 0

    def fuse(self, _other: "FakeShape") -> "FakeShape":
        self.part.fuse_calls += 1
        return self

    def removeSplitter(self) -> "FakeShape":
        return self

    def translate(self, vector: tuple[float, float, float]) -> None:
        self.translate_calls.append(vector)

    def rotate(self, _origin: object, _axis: object, degrees: float) -> None:
        self.rotate_calls.append(degrees)

    def common(self, _box: "FakeShape") -> "FakeShape":
        self.common_calls += 1
        return self

    def exportStep(self, filename: str) -> None:
        Path(filename).write_text("step\n", encoding="utf-8")


class FakeWire:
    def __init__(self, part: "FakePart", _edges: object = None) -> None:
        self.part = part

    def makePipeShell(self, _profiles: list[object], _make_solid: bool, _is_frenet: bool) -> FakeShape:
        shape = FakeShape(self.part, self.part.next_shape_z_min, self.part.next_shape_z_max)
        self.part.shapes.append(shape)
        return shape


class FakeHelix:
    Edges = ["edge"]


class FakePart:
    def __init__(self) -> None:
        self.shapes: list[FakeShape] = []
        self.helix_calls: list[tuple[float, float, float]] = []
        self.circle_calls: list[tuple[float, tuple[float, float, float], tuple[float, float, float]]] = []
        self.box_calls: list[tuple[float, float, float, tuple[float, float, float]]] = []
        self.fuse_calls = 0
        self.next_shape_z_min = 0.0
        self.next_shape_z_max = 6.0

    def makeHelix(self, pitch: float, height: float, radius: float) -> FakeHelix:
        self.helix_calls.append((pitch, height, radius))
        return FakeHelix()

    def Wire(self, edges: object) -> FakeWire:
        return FakeWire(self, edges)

    def makeCircle(
        self,
        radius: float,
        center: tuple[float, float, float],
        normal: tuple[float, float, float],
    ) -> tuple[float, tuple[float, float, float], tuple[float, float, float]]:
        self.circle_calls.append((radius, center, normal))
        return (radius, center, normal)

    def makeBox(
        self,
        x: float,
        y: float,
        z: float,
        origin: tuple[float, float, float],
    ) -> FakeShape:
        self.box_calls.append((x, y, z, origin))
        return FakeShape(self)


class FakeMesh:
    def write(self, path: str) -> None:
        Path(path).write_text("stl\n", encoding="utf-8")


class FakeMeshPart:
    def __init__(self) -> None:
        self.mesh_calls: list[dict[str, object]] = []

    def meshFromShape(self, **kwargs: object) -> FakeMesh:
        self.mesh_calls.append(kwargs)
        return FakeMesh()


def _install_fake_freecad_modules(monkeypatch: MonkeyPatch) -> tuple[FakePart, FakeMeshPart]:
    app_mod = ModuleType("FreeCAD")
    app_mod.Vector = lambda x, y, z: (x, y, z)  # type: ignore[attr-defined]

    part = FakePart()
    part_mod = ModuleType("Part")
    part_mod.makeHelix = part.makeHelix  # type: ignore[attr-defined]
    part_mod.Wire = part.Wire  # type: ignore[attr-defined]
    part_mod.makeCircle = part.makeCircle  # type: ignore[attr-defined]
    part_mod.makeBox = part.makeBox  # type: ignore[attr-defined]

    mesh_part = FakeMeshPart()
    mesh_part_mod = ModuleType("MeshPart")
    mesh_part_mod.meshFromShape = mesh_part.meshFromShape  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "FreeCAD", app_mod)
    monkeypatch.setitem(sys.modules, "Part", part_mod)
    monkeypatch.setitem(sys.modules, "MeshPart", mesh_part_mod)
    return part, mesh_part


def test_export_spring_model_writes_stl_step_and_report_from_public_api(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    part, mesh_part = _install_fake_freecad_modules(monkeypatch)
    solve_result = solve_spring(SpringSolveRequest(name="export", inputs=make_solver_inputs()))
    assert solve_result.diagnostics.resolved is not None

    export_result = export_spring_model(
        SpringModelExportRequest(
            candidate=solve_result.diagnostics.resolved.active_candidate,
            output_stl=tmp_path / "spring.stl",
            output_step=tmp_path / "spring.step",
            output_report=tmp_path / "spring.json",
            centers_xy_mm=[(0.0, 0.0), (8.0, 0.0)],
            installed_height_mm=5.5,
        )
    )

    assert export_result.status == "spring.model.status.exported"
    assert export_result.backend == "freecad"
    assert export_result.output_stl.read_text(encoding="utf-8") == "stl\n"
    assert export_result.output_step.read_text(encoding="utf-8") == "step\n"
    report = export_result.output_report.read_text(encoding="utf-8")
    assert '"backend": "freecad"' in report
    assert '"candidate_id":' in report
    assert len(mesh_part.mesh_calls) == 1
    assert part.fuse_calls >= 1
