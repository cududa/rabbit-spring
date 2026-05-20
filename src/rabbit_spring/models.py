"""Public Pydantic models for solver inputs, diagnostics, and export results."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from .tokens import SpringEndType, SpringSolverReason, SpringSolverStatus


class DomainModel(BaseModel):
    """Strict mutable model used for package inputs and outputs."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        strict=True,
        validate_default=True,
        validate_assignment=True,
    )


class ForceBand(DomainModel):
    preferred_min: float
    preferred_max: float
    center: float

    @model_validator(mode="after")
    def _validate_bounds(self) -> "ForceBand":
        if self.preferred_min <= 0.0:
            raise ValueError("preferred_min must be > 0")
        if self.preferred_max < self.preferred_min:
            raise ValueError("preferred_max must be >= preferred_min")
        if self.center < self.preferred_min or self.center > self.preferred_max:
            raise ValueError("center must be within [preferred_min, preferred_max]")
        return self

    def with_shift(self, shift: float) -> "ForceBand":
        return ForceBand(
            preferred_min=float(self.preferred_min + shift),
            preferred_max=float(self.preferred_max + shift),
            center=float(self.center + shift),
        )


class ScoreWeights(DomainModel):
    actuation_error: float = 1.00
    compressed_hard_stop_error: float = 0.75
    solid_margin: float = 2.0
    fit_margin: float = 2.0
    stress: float = 1.0
    simplicity: float = 0.05


class SpringSizingConfig(DomainModel):
    spring_count: int = 3
    switch_force_nominal_n: float = 1.57
    shear_modulus_n_per_mm2: float = 79300.0
    end_style_default: SpringEndType = "closed_ground"
    end_styles: list[SpringEndType] = Field(default_factory=lambda: ["closed_ground"])
    installed_length_rest_mm: float | None = None
    installed_length_actuation_mm: float | None = None
    installed_length_compressed_hard_stop_mm: float | None = None
    allowed_wire_diameters_default_mm: list[float] = Field(
        default_factory=lambda: [0.203, 0.229, 0.254, 0.279, 0.305, 0.330, 0.356, 0.381, 0.406],
    )
    allowed_wire_diameters_extended_mm: list[float] = Field(default_factory=list)
    mean_diameter_candidates_mm: list[float] = Field(
        default_factory=lambda: [5.05, 5.10, 5.15, 5.20, 5.25],
    )
    active_coils_min: int = 2
    active_coils_max: int = 14
    free_length_min_mm: float = 4.0
    free_length_max_mm: float = 12.0
    spring_index_reject_below: float = 4.0
    spring_index_preferred_min: float = 6.0
    spring_index_soft_warn_above: float = 16.0
    solid_margin_reject_below_mm: float = 0.30
    solid_margin_preferred_min_mm: float = 0.50
    support_annulus_inner_margin_min_radial_mm: float = 0.15
    support_annulus_inner_margin_preferred_radial_mm: float = 0.20
    support_annulus_outer_margin_min_radial_mm: float = 0.15
    support_annulus_outer_margin_preferred_radial_mm: float = 0.20
    stress_soft_warn_above_n_per_mm2: float = 900.0
    near_miss_max_delta_mm: float = 0.35
    target_total_force_actuation_n: ForceBand = Field(
        default_factory=lambda: ForceBand(preferred_min=2.20, preferred_max=2.40, center=2.30),
    )
    target_total_force_compressed_hard_stop_n: ForceBand = Field(
        default_factory=lambda: ForceBand(preferred_min=2.50, preferred_max=2.85, center=2.65),
    )
    score_weights: ScoreWeights = Field(default_factory=ScoreWeights)
    diagnostics_top_k: int = 5

    @field_validator("end_style_default", mode="before")
    @classmethod
    def _normalize_end_style_default(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("end_styles", mode="before")
    @classmethod
    def _normalize_end_styles(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value]

    @model_validator(mode="after")
    def _validate_ranges(self) -> "SpringSizingConfig":
        if self.spring_count < 1:
            raise ValueError("spring_count must be >= 1")
        if self.active_coils_max < self.active_coils_min:
            raise ValueError("active_coils_max must be >= active_coils_min")
        if self.free_length_max_mm < self.free_length_min_mm:
            raise ValueError("free_length_max_mm must be >= free_length_min_mm")
        if self.diagnostics_top_k < 0:
            raise ValueError("diagnostics_top_k must be >= 0")
        return self


SpringMassSource = Literal["cap_volume_mm3"]


class MassBudgetGeometryItemConfig(DomainModel):
    name: str = "cap"
    source: SpringMassSource = "cap_volume_mm3"
    density_g_cm3: float = 1.10
    scale: float = 1.0


class MassBudgetFixedItemConfig(DomainModel):
    name: str
    mass_g: float = 0.0


class MassBudgetConfig(DomainModel):
    geometry_items: list[MassBudgetGeometryItemConfig] = Field(
        default_factory=lambda: [MassBudgetGeometryItemConfig()],
    )
    fixed_items: list[MassBudgetFixedItemConfig] = Field(default_factory=list)
    gravity_safety_factor: float = 1.20
    gravity_margin_n: float = 0.05


class GeometryItemResult(DomainModel):
    name: str
    source: SpringMassSource
    volume_mm3: float
    density_g_cm3: float
    scale: float
    mass_g: float


class FixedItemResult(DomainModel):
    name: str
    mass_g: float


class MassBudgetResult(DomainModel):
    geometry_items: list[GeometryItemResult]
    fixed_items: list[FixedItemResult]
    geometry_mass_g: float
    fixed_mass_g: float
    total_mass_g: float
    gravity_load_n: float
    gravity_safety_factor: float
    gravity_margin_n: float
    gravity_design_force_n: float


class SpringSupportAnnulus(DomainModel):
    inner_diameter_mm: float
    outer_diameter_mm: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def radial_width_mm(self) -> float:
        return 0.5 * (self.outer_diameter_mm - self.inner_diameter_mm)

    @model_validator(mode="after")
    def _validate_support_annulus(self) -> "SpringSupportAnnulus":
        if self.inner_diameter_mm <= 0.0:
            raise ValueError("support annulus inner diameter must be > 0")
        if self.outer_diameter_mm <= self.inner_diameter_mm:
            raise ValueError("support annulus outer diameter must be > inner diameter")
        return self


class SpringGeometryInputs(DomainModel):
    spring_count: int
    post_outer_diameter_mm: float
    support_annulus: SpringSupportAnnulus
    well_inner_diameter_mm: float
    spring_top_interface_world_z_mm: float
    well_floor_z_world_mm: float
    actuation_travel_delta_mm: float
    compressed_hard_stop_travel_delta_mm: float


class SpringSolverInputs(DomainModel):
    geometry: SpringGeometryInputs
    cap_volume_mm3: float | None = None
    mass_budget: MassBudgetConfig | None = None
    spring_sizing: SpringSizingConfig | None = None


class SpringSearchGeometry(DomainModel):
    post_outer_diameter_mm: float
    support_annulus: SpringSupportAnnulus
    well_inner_diameter_mm: float
    spring_top_interface_world_z_mm: float
    well_floor_z_world_mm: float
    installed_length_rest_mm: float
    installed_length_actuation_mm: float
    installed_length_compressed_hard_stop_mm: float


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


class CandidatePhysics(DomainModel):
    inner_diameter_mm: float
    outer_diameter_mm: float
    spring_index: float
    inactive_coils: float
    total_coils: float
    solid_height_mm: float
    solid_margin_mm: float
    deflection_rest_mm: float
    deflection_actuation_mm: float
    deflection_compressed_hard_stop_mm: float
    single_spring_force_rest_n: float
    single_spring_force_actuation_n: float
    single_spring_force_compressed_hard_stop_n: float
    total_force_actuation_with_switch_n: float
    total_force_compressed_hard_stop_with_switch_n: float
    stress_rest_n_per_mm2: float
    stress_actuation_n_per_mm2: float
    stress_compressed_hard_stop_n_per_mm2: float


class CandidateFit(DomainModel):
    support_inner_margin_radial_mm: float
    support_outer_margin_radial_mm: float
    preferred_fit_pass: bool
    near_miss_advisory: bool
    reject_reasons: list[str]


class CandidateScore(DomainModel):
    candidate_score: float
    force_score: float
    warnings: list[str]
    notes: list[str]


class CandidateGeometry(DomainModel):
    wire_diameter_mm: float
    mean_diameter_mm: float
    active_coils: int
    free_length_mm: float
    spring_rate_n_per_mm: float
    end_type: SpringEndType


class SpringCandidate(DomainModel):
    candidate_id: str
    geometry: CandidateGeometry
    physics: CandidatePhysics
    fit: CandidateFit
    score: CandidateScore

    @property
    def installed_length_rest_mm(self) -> float:
        return self.geometry.free_length_mm - self.physics.deflection_rest_mm

    @property
    def installed_length_actuation_mm(self) -> float:
        return self.geometry.free_length_mm - self.physics.deflection_actuation_mm

    @property
    def installed_length_compressed_hard_stop_mm(self) -> float:
        return self.geometry.free_length_mm - self.physics.deflection_compressed_hard_stop_mm


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
    top_candidates: list[SpringCandidate] = Field(default_factory=list)
    near_miss_candidates: list[SpringCandidate] = Field(default_factory=list)
    reject_reason_histogram: dict[str, int] = Field(default_factory=dict)


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
    centers_xy_mm: list[tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0)])
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
    centers_xy_mm: list[tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0)])
    installed_height_mm: float | None = None


class SpringSolveAndExportResult(DomainModel):
    solve: SpringSolveResult
    export: SpringModelExportResult | None
