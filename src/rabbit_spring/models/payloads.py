"""Top-level solver and export payload models."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator

from ..tokens import SpringEndType, SpringSolverReason, SpringSolverStatus
from .base import DomainModel
from .candidates import SpringCandidate
from .config import ForceBand, MassBudgetConfig, SpringSizingConfig
from .geometry import SpringGeometryInputs, SpringSearchGeometry
from .mass import MassBudgetResult


def _empty_candidates() -> list[SpringCandidate]:
    return []


def _empty_reject_histogram() -> dict[str, int]:
    return {}


def _default_centers() -> list[tuple[float, float]]:
    return [(0.0, 0.0)]


class SpringSolverInputs(DomainModel):
    geometry: SpringGeometryInputs
    cap_volume_mm3: float | None = None
    mass_budget: MassBudgetConfig | None = None
    spring_sizing: SpringSizingConfig | None = None


class SpringForceTargets(DomainModel):
    total_force_actuation_n: ForceBand
    total_force_compressed_hard_stop_n: ForceBand
    per_spring_force_actuation_center_n: float
    per_spring_force_compressed_hard_stop_center_n: float
    mass_adjustment_delta_n: float

    @model_validator(mode="after")
    def _validate_target_order(self) -> "SpringForceTargets":
        if self.total_force_compressed_hard_stop_n.center <= self.total_force_actuation_n.center:
            raise ValueError("compressed hard-stop target center must be above actuation center")
        return self


class ResolvedSpringPayload(DomainModel):
    active_candidate: SpringCandidate


class SpringSearchDiagnosticsPayload(DomainModel):
    status: SpringSolverStatus
    name: str
    reason: SpringSolverReason | None = None
    mass_budget: MassBudgetResult | None = None
    spring_sizing: SpringSizingConfig | None = None
    force_targets: SpringForceTargets | None = None
    geometry: SpringSearchGeometry | None = None
    resolved: ResolvedSpringPayload | None = None
    top_candidates: list[SpringCandidate] = Field(default_factory=_empty_candidates)
    near_miss_candidates: list[SpringCandidate] = Field(default_factory=_empty_candidates)
    reject_reason_histogram: dict[str, int] = Field(default_factory=_empty_reject_histogram)


class SpringSolveRequest(DomainModel):
    name: str = "spring"
    inputs: SpringSolverInputs


class SpringSolveResult(DomainModel):
    diagnostics: SpringSearchDiagnosticsPayload


class SpringModelExportRequest(DomainModel):
    candidate: SpringCandidate
    output_stl: Path
    output_step: Path
    output_report: Path
    centers_xy_mm: list[tuple[float, float]] = Field(default_factory=_default_centers)
    installed_height_mm: float | None = None
    z0_mm: float = 0.0
    linear_deflection_mm: float = 0.02
    angular_deflection_deg: float = 15.0

    @model_validator(mode="after")
    def _validate_export_request(self) -> "SpringModelExportRequest":
        if len(self.centers_xy_mm) < 1:
            raise ValueError("centers_xy_mm must include at least one spring center")
        installed_height_mm = self.installed_height_mm
        if installed_height_mm is not None and installed_height_mm <= 0.0:
            raise ValueError("installed_height_mm must be > 0 when provided")
        if self.linear_deflection_mm <= 0.0:
            raise ValueError("linear_deflection_mm must be > 0")
        if self.angular_deflection_deg <= 0.0:
            raise ValueError("angular_deflection_deg must be > 0")
        return self


class SpringModelExportResult(DomainModel):
    status: str
    backend: str
    output_stl: Path
    output_step: Path
    output_report: Path
    centers_xy_mm: list[tuple[float, float]]
    installed_height_mm: float
    wire_diameter_mm: float
    mean_diameter_mm: float
    pitch_mm: float
    total_turns: float
    end_type: SpringEndType


class SpringSolveAndExportRequest(DomainModel):
    solve: SpringSolveRequest
    export_output_stl: Path
    export_output_step: Path
    export_output_report: Path
    centers_xy_mm: list[tuple[float, float]] = Field(default_factory=_default_centers)
    installed_height_mm: float | None = None


class SpringSolveAndExportResult(DomainModel):
    solve: SpringSolveResult
    export: SpringModelExportResult | None
