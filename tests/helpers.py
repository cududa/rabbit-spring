from __future__ import annotations

from rabbit_spring.models import (
    ForceBand,
    MassBudgetConfig,
    MassBudgetFixedItemConfig,
    SpringGeometryInputs,
    SpringSizingConfig,
    SpringSolverInputs,
    SpringSupportAnnulus,
)


def make_solver_inputs(
    *,
    cap_volume_mm3: float = 2000.0,
    spring_sizing: SpringSizingConfig | None = None,
) -> SpringSolverInputs:
    return SpringSolverInputs(
        geometry=SpringGeometryInputs(
            spring_count=3,
            post_outer_diameter_mm=2.0,
            support_annulus=SpringSupportAnnulus(
                inner_diameter_mm=4.4,
                outer_diameter_mm=6.0,
            ),
            well_inner_diameter_mm=6.45,
            spring_top_interface_world_z_mm=8.0,
            well_floor_z_world_mm=1.0,
            actuation_travel_delta_mm=0.5,
            compressed_hard_stop_travel_delta_mm=1.0,
        ),
        cap_volume_mm3=cap_volume_mm3,
        mass_budget=MassBudgetConfig(
            fixed_items=[MassBudgetFixedItemConfig(name="steel_rods", mass_g=2.0)]
        ),
        spring_sizing=spring_sizing
        or SpringSizingConfig(
            target_total_force_actuation_n=ForceBand(
                preferred_min=2.2,
                preferred_max=2.4,
                center=2.3,
            ),
            target_total_force_compressed_hard_stop_n=ForceBand(
                preferred_min=2.5,
                preferred_max=2.85,
                center=2.65,
            ),
        ),
    )
