"""Spring candidate result models."""

from __future__ import annotations

from ..tokens import SpringEndType
from .base import DomainModel


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
