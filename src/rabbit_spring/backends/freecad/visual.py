"""Visual export parameter resolution."""

from __future__ import annotations

from ...constants import VISUAL_MIN_TURNS
from ...errors import SpringModelExportError
from ...models.payloads import SpringModelExportRequest
from ...pitch import enforce_min_pitch_for_length
from .types import SpringVisualParams


def resolve_visual_params(request: SpringModelExportRequest) -> SpringVisualParams:
    candidate = request.candidate
    installed_height_mm = request.installed_height_mm or candidate.installed_length_rest_mm
    if installed_height_mm <= 0.0:
        raise SpringModelExportError("installed spring height must be > 0")

    wire_diameter_mm = candidate.geometry.wire_diameter_mm
    mean_diameter_mm = candidate.geometry.mean_diameter_mm
    if wire_diameter_mm <= 0.0 or mean_diameter_mm <= wire_diameter_mm:
        raise SpringModelExportError("candidate has invalid wire/mean diameter geometry")

    turns = max(VISUAL_MIN_TURNS, candidate.physics.total_coils)
    turns, pitch_mm = enforce_min_pitch_for_length(
        length_mm=installed_height_mm,
        turns=turns,
        wire_diameter_mm=wire_diameter_mm,
        min_turns=1.0,
    )

    return SpringVisualParams(
        centers_xy_mm=request.centers_xy_mm,
        z0_mm=request.z0_mm,
        installed_height_mm=installed_height_mm,
        wire_diameter_mm=wire_diameter_mm,
        mean_diameter_mm=mean_diameter_mm,
        wire_radius_mm=0.5 * wire_diameter_mm,
        mean_radius_mm=0.5 * mean_diameter_mm,
        pitch_mm=pitch_mm,
        turns=turns,
        inactive_coils=max(0.0, candidate.physics.inactive_coils),
        end_type=candidate.geometry.end_type,
    )
