from __future__ import annotations

from pathlib import Path

from rabbit_spring import (
    CandidateFit,
    CandidateGeometry,
    CandidatePhysics,
    CandidateScore,
    SpringCandidate,
    SpringEndType,
    SpringModelExportRequest,
)
from rabbit_spring.backends.freecad import (
    FreeCadModules,
    SpringVisualParams,
    build_spring_helix,
    export_spring_model,
    resolve_visual_params,
)


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
        self.exported_step: Path | None = None

    def fuse(self, other: "FakeShape") -> "FakeShape":
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
        self.exported_step = Path(filename)
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


class FakeApp:
    def Vector(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        return (x, y, z)


class FakeMesh:
    def write(self, path: str) -> None:
        Path(path).write_text("stl\n", encoding="utf-8")


class FakeMeshPart:
    def __init__(self) -> None:
        self.mesh_calls: list[dict[str, object]] = []

    def meshFromShape(self, **kwargs: object) -> FakeMesh:
        self.mesh_calls.append(kwargs)
        return FakeMesh()


def _candidate(
    *,
    end_type: SpringEndType = "closed_ground",
    inactive_coils: float = 2.0,
) -> SpringCandidate:
    return SpringCandidate(
        candidate_id="test",
        geometry=CandidateGeometry(
            wire_diameter_mm=0.3,
            mean_diameter_mm=5.1,
            active_coils=6,
            free_length_mm=7.0,
            spring_rate_n_per_mm=0.1,
            end_type=end_type,
        ),
        physics=CandidatePhysics(
            inner_diameter_mm=4.8,
            outer_diameter_mm=5.4,
            spring_index=17.0,
            inactive_coils=inactive_coils,
            total_coils=6 + inactive_coils,
            solid_height_mm=2.4,
            solid_margin_mm=3.6,
            deflection_rest_mm=1.0,
            deflection_actuation_mm=1.5,
            deflection_compressed_hard_stop_mm=2.0,
            single_spring_force_rest_n=0.1,
            single_spring_force_actuation_n=0.15,
            single_spring_force_compressed_hard_stop_n=0.2,
            total_force_actuation_with_switch_n=2.02,
            total_force_compressed_hard_stop_with_switch_n=2.17,
            stress_rest_n_per_mm2=100.0,
            stress_actuation_n_per_mm2=150.0,
            stress_compressed_hard_stop_n_per_mm2=200.0,
        ),
        fit=CandidateFit(
            support_inner_margin_radial_mm=0.2,
            support_outer_margin_radial_mm=0.2,
            preferred_fit_pass=True,
            near_miss_advisory=False,
            reject_reasons=[],
        ),
        score=CandidateScore(candidate_score=1.0, force_score=1.0, warnings=[], notes=[]),
    )


def test_resolve_visual_params_uses_rest_height_by_default() -> None:
    request = SpringModelExportRequest(
        candidate=_candidate(),
        output_stl=Path("spring.stl"),
        output_step=Path("spring.step"),
        output_report=Path("spring.json"),
    )

    params = resolve_visual_params(request)

    assert params.installed_height_mm == 6.0
    assert params.centers_xy_mm == [(0.0, 0.0)]
    assert params.wire_radius_mm == 0.15


def test_build_spring_helix_closed_ground_trims_and_rotates() -> None:
    part = FakePart()
    app = FakeApp()
    params = SpringVisualParams(
        centers_xy_mm=[(0.0, 0.0)],
        z0_mm=0.0,
        installed_height_mm=6.0,
        wire_diameter_mm=0.3,
        mean_diameter_mm=5.1,
        wire_radius_mm=0.15,
        mean_radius_mm=2.55,
        pitch_mm=0.4,
        turns=8.432098765432098,
        inactive_coils=2.0,
        end_type="closed_ground",
    )

    build_spring_helix(part_mod=part, app_mod=app, profile_wire=FakeWire(part), params=params)

    assert len(part.shapes) >= 3
    assert part.box_calls
    assert sum(shape.common_calls for shape in part.shapes) >= 1
    top_segments = part.shapes[2::3]
    assert top_segments
    assert top_segments[0].rotate_calls


def test_export_spring_model_writes_stl_step_and_report(tmp_path: Path) -> None:
    part = FakePart()
    app = FakeApp()
    mesh_part = FakeMeshPart()
    request = SpringModelExportRequest(
        candidate=_candidate(end_type="open", inactive_coils=0.0),
        output_stl=tmp_path / "spring.stl",
        output_step=tmp_path / "spring.step",
        output_report=tmp_path / "spring.json",
        centers_xy_mm=[(0.0, 0.0), (8.0, 0.0)],
        installed_height_mm=5.5,
    )

    result = export_spring_model(
        request,
        modules=FreeCadModules(app_mod=app, part_mod=part, mesh_part_mod=mesh_part),
    )

    assert result.backend == "freecad"
    assert result.output_stl.exists()
    assert result.output_step.exists()
    assert result.output_report.exists()
    assert len(mesh_part.mesh_calls) == 1
    assert part.fuse_calls >= 1
