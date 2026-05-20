"""FreeCAD-backed spring model export backend."""

from __future__ import annotations

from .export import export_spring_model
from .loader import load_freecad_modules
from .shapes import build_spring_helix, build_spring_model_shape, profile_normal_for_helix
from .types import FreeCadModules, SpringVisualParams
from .visual import resolve_visual_params

__all__ = [
    "FreeCadModules",
    "SpringVisualParams",
    "build_spring_helix",
    "build_spring_model_shape",
    "export_spring_model",
    "load_freecad_modules",
    "profile_normal_for_helix",
    "resolve_visual_params",
]
