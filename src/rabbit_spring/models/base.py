"""Shared Pydantic base model configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Strict mutable model used for package inputs and outputs."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        strict=True,
        validate_default=True,
        validate_assignment=True,
    )
