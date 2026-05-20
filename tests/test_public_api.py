from __future__ import annotations

from typing import get_args

import rabbit_spring
import rabbit_spring.models as models
from rabbit_spring import export_spring_model, solve_and_export, solve_spring
from rabbit_spring.models import (
    CandidateFit,
    CandidateGeometry,
    CandidatePhysics,
    CandidateScore,
    DomainModel,
    FixedItemResult,
    ForceBand,
    GeometryItemResult,
    MassBudgetConfig,
    MassBudgetFixedItemConfig,
    MassBudgetGeometryItemConfig,
    MassBudgetResult,
    ResolvedSpringPayload,
    ScoreWeights,
    SpringCandidate,
    SpringForceTargets,
    SpringGeometryInputs,
    SpringMassSource,
    SpringModelExportRequest,
    SpringModelExportResult,
    SpringSearchDiagnosticsPayload,
    SpringSearchGeometry,
    SpringSizingConfig,
    SpringSolveAndExportRequest,
    SpringSolveAndExportResult,
    SpringSolveRequest,
    SpringSolveResult,
    SpringSolverInputs,
    SpringSupportAnnulus,
)


def test_root_namespace_exports_only_documented_functions() -> None:
    assert sorted(rabbit_spring.__all__) == [
        "export_spring_model",
        "solve_and_export",
        "solve_spring",
    ]
    assert callable(solve_spring)
    assert callable(export_spring_model)
    assert callable(solve_and_export)


def test_models_namespace_exports_documented_models() -> None:
    expected_names = {
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
    }
    assert set(models.__all__) == expected_names

    imported_models = [
        CandidateFit,
        CandidateGeometry,
        CandidatePhysics,
        CandidateScore,
        DomainModel,
        FixedItemResult,
        ForceBand,
        GeometryItemResult,
        MassBudgetConfig,
        MassBudgetFixedItemConfig,
        MassBudgetGeometryItemConfig,
        MassBudgetResult,
        ResolvedSpringPayload,
        ScoreWeights,
        SpringCandidate,
        SpringForceTargets,
        SpringGeometryInputs,
        SpringModelExportRequest,
        SpringModelExportResult,
        SpringSearchDiagnosticsPayload,
        SpringSearchGeometry,
        SpringSizingConfig,
        SpringSolveAndExportRequest,
        SpringSolveAndExportResult,
        SpringSolveRequest,
        SpringSolveResult,
        SpringSolverInputs,
        SpringSupportAnnulus,
    ]
    assert all(issubclass(model, DomainModel) for model in imported_models)
    assert get_args(SpringMassSource) == ("cap_volume_mm3",)
