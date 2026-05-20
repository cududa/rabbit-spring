"""Shared spring turns/pitch helpers."""

from __future__ import annotations

from .constants import MIN_FREE_PITCH_TO_WIRE_RATIO


def enforce_min_pitch_for_length(
    *,
    length_mm: float,
    turns: float,
    wire_diameter_mm: float,
    min_turns: float,
) -> tuple[float, float]:
    min_pitch_mm = wire_diameter_mm * MIN_FREE_PITCH_TO_WIRE_RATIO
    pitch_mm = length_mm / turns
    if pitch_mm < min_pitch_mm:
        adjusted_turns = max(min_turns, length_mm / max(min_pitch_mm, 1e-6))
        return adjusted_turns, length_mm / adjusted_turns
    return turns, pitch_mm
