from __future__ import annotations

from rabbit_spring import solve_spring
from rabbit_spring.models import (
    MassBudgetConfig,
    SpringGeometryInputs,
    SpringSizingConfig,
    SpringSolveRequest,
    SpringSolverInputs,
    SpringSupportAnnulus,
)


def main() -> None:
    inputs = SpringSolverInputs(
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
        cap_volume_mm3=2000.0,
        mass_budget=MassBudgetConfig(),
        spring_sizing=SpringSizingConfig(),
    )
    result = solve_spring(SpringSolveRequest(name="smoke", inputs=inputs))
    print(result.diagnostics.status)


if __name__ == "__main__":
    main()
