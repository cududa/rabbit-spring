# rabbit-spring

`rabbit-spring` is a generic compression spring solution finder for small
compression-spring mechanisms. It is intentionally independent of any consuming
product, CAD pipeline, or application-specific assembly model.

The package provides:

- a pure Python spring solver with Pydantic input/output models
- candidate search, fit checks, mass-budget compensation, and diagnostics
- optional FreeCAD-backed model export to STL and STEP
- JSON reports for downstream CAD and manufacturing workflows

## Quick Start

```python
from rabbit_spring import (
    ForceBand,
    MassBudgetConfig,
    SpringGeometryInputs,
    SpringModelExportRequest,
    SpringSizingConfig,
    SpringSolveRequest,
    SpringSolverInputs,
    SpringSupportAnnulus,
    solve_spring,
)

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
    spring_sizing=SpringSizingConfig(
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

result = solve_spring(SpringSolveRequest(name="demo", inputs=inputs))
print(result.diagnostics.status)
print(result.diagnostics.resolved.active_candidate)
```

## FreeCAD Export

Model export requires running in an environment where `FreeCAD`, `Part`, and
`MeshPart` are importable. FreeCAD is not installed by this package.

```python
from pathlib import Path
from rabbit_spring import SpringModelExportRequest, export_spring_model

candidate = result.diagnostics.resolved.active_candidate
export = export_spring_model(
    SpringModelExportRequest(
        candidate=candidate,
        output_stl=Path("spring.stl"),
        output_step=Path("spring.step"),
        output_report=Path("spring.json"),
        centers_xy_mm=[(0.0, 0.0), (8.0, 0.0), (4.0, 6.928)],
    )
)
print(export.output_stl)
```

For Rhino pipelines, import the generated STL or STEP artifact.
