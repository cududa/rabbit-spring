"""Stable public namespace for Pydantic request, config, and result models."""

from __future__ import annotations

from .candidates import (
    CandidateFit,
    CandidateGeometry,
    CandidatePhysics,
    CandidateScore,
    SpringCandidate,
)
from .config import (
    ForceBand,
    MassBudgetConfig,
    MassBudgetFixedItemConfig,
    MassBudgetGeometryItemConfig,
    ScoreWeights,
    SpringMassSource,
    SpringSizingConfig,
)
from .base import DomainModel
from .geometry import SpringGeometryInputs, SpringSearchGeometry, SpringSupportAnnulus
from .mass import FixedItemResult, GeometryItemResult, MassBudgetResult
from .payloads import (
    ResolvedSpringPayload,
    SpringForceTargets,
    SpringModelExportRequest,
    SpringModelExportResult,
    SpringSearchDiagnosticsPayload,
    SpringSolveAndExportRequest,
    SpringSolveAndExportResult,
    SpringSolveRequest,
    SpringSolveResult,
    SpringSolverInputs,
)

__all__ = [
    "CandidateFit",
    "CandidateGeometry",
    "CandidatePhysics",
    "CandidateScore",
    "DomainModel",
    "FixedItemResult",
    "ForceBand",
    "GeometryItemResult",
    "MassBudgetConfig",
    "MassBudgetFixedItemConfig",
    "MassBudgetGeometryItemConfig",
    "MassBudgetResult",
    "ResolvedSpringPayload",
    "ScoreWeights",
    "SpringCandidate",
    "SpringForceTargets",
    "SpringGeometryInputs",
    "SpringMassSource",
    "SpringModelExportRequest",
    "SpringModelExportResult",
    "SpringSearchDiagnosticsPayload",
    "SpringSearchGeometry",
    "SpringSizingConfig",
    "SpringSolveAndExportRequest",
    "SpringSolveAndExportResult",
    "SpringSolveRequest",
    "SpringSolveResult",
    "SpringSolverInputs",
    "SpringSupportAnnulus",
]
