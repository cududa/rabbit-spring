"""Candidate physics calculations for spring search."""

from __future__ import annotations

import math

from .constants import INACTIVE_COILS_BY_END_TYPE
from .models import CandidatePhysics, SpringSearchGeometry
from .tokens import SpringEndType


def _stress_n_per_mm2(
    *,
    wahl_factor: float,
    force_n: float,
    mean_diameter_mm: float,
    wire_diameter_mm: float,
) -> float:
    return wahl_factor * (
        (8.0 * force_n * mean_diameter_mm) / max(math.pi * (wire_diameter_mm**3), 1e-6)
    )


def compute_candidate_physics(
    *,
    spring_count: int,
    wire_diameter_mm: float,
    mean_diameter_mm: float,
    active_coils: int,
    end_type: SpringEndType,
    free_length_mm: float,
    spring_rate_n_per_mm: float,
    geometry: SpringSearchGeometry,
    switch_force_nominal_n: float,
) -> CandidatePhysics:
    wire_diameter = wire_diameter_mm
    mean_diameter = mean_diameter_mm
    free_length = free_length_mm
    spring_rate = spring_rate_n_per_mm

    inner_diameter_mm = mean_diameter - wire_diameter
    outer_diameter_mm = mean_diameter + wire_diameter
    spring_index = (mean_diameter / wire_diameter) if wire_diameter > 0 else 0.0
    inactive_coils = INACTIVE_COILS_BY_END_TYPE[end_type]
    total_coils = active_coils + inactive_coils
    solid_height_mm = total_coils * wire_diameter
    solid_margin_mm = geometry.installed_length_compressed_hard_stop_mm - solid_height_mm

    deflection_rest_mm = free_length - geometry.installed_length_rest_mm
    deflection_actuation_mm = free_length - geometry.installed_length_actuation_mm
    deflection_compressed_hard_stop_mm = (
        free_length - geometry.installed_length_compressed_hard_stop_mm
    )

    single_spring_force_rest_n = spring_rate * deflection_rest_mm
    single_spring_force_actuation_n = spring_rate * deflection_actuation_mm
    single_spring_force_compressed_hard_stop_n = spring_rate * deflection_compressed_hard_stop_mm

    total_force_actuation_with_switch_n = (
        spring_count * single_spring_force_actuation_n + switch_force_nominal_n
    )
    total_force_compressed_hard_stop_with_switch_n = (
        spring_count * single_spring_force_compressed_hard_stop_n + switch_force_nominal_n
    )

    wahl_factor = (
        (((4.0 * spring_index) - 1.0) / max((4.0 * spring_index) - 4.0, 1e-6))
        + (0.615 / max(spring_index, 1e-6))
    )
    stress_rest_n_per_mm2 = _stress_n_per_mm2(
        wahl_factor=wahl_factor,
        force_n=single_spring_force_rest_n,
        mean_diameter_mm=mean_diameter,
        wire_diameter_mm=wire_diameter,
    )
    stress_actuation_n_per_mm2 = _stress_n_per_mm2(
        wahl_factor=wahl_factor,
        force_n=single_spring_force_actuation_n,
        mean_diameter_mm=mean_diameter,
        wire_diameter_mm=wire_diameter,
    )
    stress_compressed_hard_stop_n_per_mm2 = _stress_n_per_mm2(
        wahl_factor=wahl_factor,
        force_n=single_spring_force_compressed_hard_stop_n,
        mean_diameter_mm=mean_diameter,
        wire_diameter_mm=wire_diameter,
    )

    return CandidatePhysics(
        inner_diameter_mm=inner_diameter_mm,
        outer_diameter_mm=outer_diameter_mm,
        spring_index=spring_index,
        inactive_coils=inactive_coils,
        total_coils=total_coils,
        solid_height_mm=solid_height_mm,
        solid_margin_mm=solid_margin_mm,
        deflection_rest_mm=deflection_rest_mm,
        deflection_actuation_mm=deflection_actuation_mm,
        deflection_compressed_hard_stop_mm=deflection_compressed_hard_stop_mm,
        single_spring_force_rest_n=single_spring_force_rest_n,
        single_spring_force_actuation_n=single_spring_force_actuation_n,
        single_spring_force_compressed_hard_stop_n=single_spring_force_compressed_hard_stop_n,
        total_force_actuation_with_switch_n=total_force_actuation_with_switch_n,
        total_force_compressed_hard_stop_with_switch_n=total_force_compressed_hard_stop_with_switch_n,
        stress_rest_n_per_mm2=stress_rest_n_per_mm2,
        stress_actuation_n_per_mm2=stress_actuation_n_per_mm2,
        stress_compressed_hard_stop_n_per_mm2=stress_compressed_hard_stop_n_per_mm2,
    )
