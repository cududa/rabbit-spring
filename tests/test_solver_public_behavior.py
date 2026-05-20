from __future__ import annotations

import math

import pytest

from rabbit_spring import solve_spring
from rabbit_spring.models import SpringSizingConfig, SpringSolveRequest
from tests.helpers import make_solver_inputs


def test_solve_spring_returns_ranked_candidate_with_consistent_lengths() -> None:
    result = solve_spring(SpringSolveRequest(name="demo", inputs=make_solver_inputs()))

    assert result.diagnostics.status == "spring.solver.status.computed"
    assert result.diagnostics.resolved is not None
    assert result.diagnostics.top_candidates

    candidate = result.diagnostics.resolved.active_candidate
    assert math.isclose(
        candidate.physics.solid_height_mm,
        candidate.physics.total_coils * candidate.geometry.wire_diameter_mm,
    )
    assert candidate.installed_length_rest_mm > candidate.installed_length_actuation_mm
    assert candidate.installed_length_actuation_mm > candidate.installed_length_compressed_hard_stop_mm


def test_solver_uses_extended_wire_list_after_default_search_finds_no_fit() -> None:
    result = solve_spring(
        SpringSolveRequest(
            name="extended",
            inputs=make_solver_inputs(
                spring_sizing=SpringSizingConfig(
                    spring_count=3,
                    allowed_wire_diameters_default_mm=[0.5],
                    allowed_wire_diameters_extended_mm=[0.30],
                    mean_diameter_candidates_mm=[5.10],
                    active_coils_min=3,
                    active_coils_max=3,
                )
            ),
        )
    )

    assert result.diagnostics.status == "spring.solver.status.computed"
    assert result.diagnostics.resolved is not None
    assert result.diagnostics.resolved.active_candidate.geometry.wire_diameter_mm == 0.30


def test_mass_budget_adjusts_reported_force_targets() -> None:
    light = solve_spring(
        SpringSolveRequest(name="light", inputs=make_solver_inputs(cap_volume_mm3=2000.0))
    )
    heavy = solve_spring(
        SpringSolveRequest(name="heavy", inputs=make_solver_inputs(cap_volume_mm3=250000.0))
    )

    assert light.diagnostics.force_targets is not None
    assert heavy.diagnostics.force_targets is not None
    assert light.diagnostics.force_targets.mass_adjustment_delta_n == 0.0
    assert heavy.diagnostics.force_targets.mass_adjustment_delta_n > 0.0
    assert (
        heavy.diagnostics.force_targets.per_spring_force_actuation_center_n
        > light.diagnostics.force_targets.per_spring_force_actuation_center_n
    )


def test_no_candidate_status_includes_reject_histogram() -> None:
    result = solve_spring(
        SpringSolveRequest(
            name="impossible",
            inputs=make_solver_inputs(
                spring_sizing=SpringSizingConfig(
                    spring_count=3,
                    allowed_wire_diameters_default_mm=[0.203],
                    allowed_wire_diameters_extended_mm=[],
                    mean_diameter_candidates_mm=[5.05],
                    active_coils_min=14,
                    active_coils_max=14,
                    free_length_min_mm=0.1,
                    free_length_max_mm=0.2,
                )
            ),
        )
    )

    assert result.diagnostics.status == "spring.solver.status.no_candidates"
    assert result.diagnostics.resolved is None
    assert result.diagnostics.reject_reason_histogram


def test_invalid_geometry_surfaces_as_domain_exception() -> None:
    inputs = make_solver_inputs()
    inputs.geometry.actuation_travel_delta_mm = 0.0

    with pytest.raises(Exception, match="actuation_travel_delta_mm must be > 0"):
        solve_spring(SpringSolveRequest(name="invalid", inputs=inputs))
