"""Strict OpenAPI request and response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(item.title() for item in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True, extra="forbid")


class RemoteRepository(ApiModel):
    url: str
    credential_ref: str | None = None


class RepositoryCreate(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    local_path: str | None = None
    remote: RemoteRepository | None = None
    revision: str | None = None

    @model_validator(mode="after")
    def one_origin(self) -> RepositoryCreate:
        if (self.local_path is None) == (self.remote is None):
            raise ValueError("exactly one of localPath or remote is required")
        return self


class Repository(ApiModel):
    id: str
    name: str
    origin_redacted: str | None
    revision: str | None
    created_at: datetime


class Page(ApiModel):
    items: list[Any]
    next_cursor: str | None


class Deletion(ApiModel):
    id: str
    status: Literal["accepted"] = "accepted"


def _default_modes() -> list[
    Literal["exact", "renamed", "structural", "semantic", "semantic-verified"]
]:
    return ["exact", "renamed"]


class ScanCreate(ApiModel):
    repository_id: str
    modes: list[
        Literal["exact", "renamed", "structural", "semantic", "semantic-verified"]
    ] = Field(
        default_factory=_default_modes
    )
    strict: bool = False


class Scan(ApiModel):
    id: str
    repository_id: str
    status: Literal["queued", "running", "completed", "partial", "failed", "cancelled"]
    algorithm_version: str = "fp-v1"
    normalization_version: str = "norm-v1"
    counts: dict[str, int]
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None


class SearchRequest(ApiModel):
    repository_ids: list[str] = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=2_000_000)
    language: Literal["python", "javascript", "typescript", "java"]
    mode: Literal["exact", "renamed"] = "exact"
    limit: int = Field(default=20, ge=1, le=100)


class SearchResult(ApiModel):
    items: list[dict[str, Any]]
    truncated: bool


class CompareRequest(ApiModel):
    left_code: str = Field(min_length=1, max_length=1_000_000)
    right_code: str = Field(min_length=1, max_length=1_000_000)
    language: Literal["python", "javascript", "typescript", "java"]
    mode: Literal["exact", "renamed"] = "exact"


class CompareResult(ApiModel):
    items: list[dict[str, Any]]


class Health(ApiModel):
    status: Literal["ok", "not_ready"]
