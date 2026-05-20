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

The canonical public API is the package root for functions and
`rabbit_spring.models` for typed request/config/result models:

```python
from rabbit_spring import solve_spring
from rabbit_spring.models import (
    ForceBand,
    MassBudgetConfig,
    SpringGeometryInputs,
    SpringSizingConfig,
    SpringSolveRequest,
    SpringSolverInputs,
    SpringSupportAnnulus,
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

## Local Development

Create the development environment and install the package editable:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

This repository uses Python 3.11 for local CAD validation because the discovered
FreeCAD 1.1 install is AMD64 and uses CPython 3.11. The pure solver is normal
Python package code and does not import FreeCAD.

FreeCAD is an optional runtime backend, not a pip dependency. To make the local
`.venv` import the installed FreeCAD modules, run:

```powershell
.\tools\configure_freecad_venv.ps1
```

If FreeCAD is installed somewhere else, set `RABBIT_SPRING_FREECAD_ROOT` or pass
`-FreeCadRoot`.

Validation commands:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m pyright --project pyrightconfig.json
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -c "import FreeCAD, Part, MeshPart; print(FreeCAD.Version())"
.\.venv\Scripts\python -m pytest -m freecad
```

## FreeCAD Export

Model export requires running in an environment where `FreeCAD`, `Part`, and
`MeshPart` are importable. FreeCAD is not installed by this package.

```python
from pathlib import Path
from rabbit_spring import export_spring_model
from rabbit_spring.models import SpringModelExportRequest

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
