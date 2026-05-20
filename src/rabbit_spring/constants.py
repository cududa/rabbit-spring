"""Shared constants for spring calculations and model rendering."""

from __future__ import annotations

from .tokens import SpringEndType

GRAVITY_M_S2 = 9.80665
MIN_FREE_PITCH_TO_WIRE_RATIO = 1.05

INACTIVE_COILS_BY_END_TYPE: dict[SpringEndType, float] = {
    "open": 0.0,
    "closed": 2.0,
    "closed_ground": 2.0,
}

VISUAL_RADIAL_CLEARANCE_MM = 0.10
VISUAL_MIN_TURNS = 4.0
