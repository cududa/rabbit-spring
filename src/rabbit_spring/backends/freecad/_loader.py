"""FreeCAD module discovery and loading."""

from __future__ import annotations

import importlib

from ...errors import SpringModelExportError
from ._types import FreeCadModules


def load_freecad_modules() -> FreeCadModules:
    try:
        return FreeCadModules(
            app_mod=importlib.import_module("FreeCAD"),
            part_mod=importlib.import_module("Part"),
            mesh_part_mod=importlib.import_module("MeshPart"),
        )
    except ImportError as exc:
        raise SpringModelExportError(
            "FreeCAD export requires FreeCAD, Part, and MeshPart to be importable"
        ) from exc
