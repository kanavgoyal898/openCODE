"""Framework-neutral parser and ingestion value objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

TokenKind = Literal[
    "keyword",
    "identifier",
    "operator",
    "punctuation",
    "string",
    "number",
    "boolean",
    "null",
    "other",
]


class SourceInputError(ValueError):
    """Base class for stable, user-safe source input failures."""

    code = "SOURCE_INPUT_ERROR"


class InvalidEncodingError(SourceInputError):
    code = "INVALID_ENCODING"


class UnsupportedLanguageError(SourceInputError):
    code = "UNSUPPORTED_LANGUAGE"


class ParseCoverageError(SourceInputError):
    code = "PARSE_COVERAGE_TOO_LOW"


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    canonical: str
    start_byte: int
    end_byte: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    role: str | None = None
    scope_id: str = "module"
    subtype: str | None = None

    def __post_init__(self) -> None:
        if self.start_byte < 0 or self.end_byte <= self.start_byte:
            raise ValueError("token byte span must be non-empty and ordered")
        if min(self.start_line, self.start_column, self.end_line, self.end_column) < 1:
            raise ValueError("token coordinates are one-based")


@dataclass(frozen=True, slots=True)
class TokenizationResult:
    language: str
    adapter_version: str
    tokens: tuple[Token, ...]
    degraded: bool
    error_count: int
    lexical_coverage: float


@dataclass(frozen=True, slots=True)
class Diagnostic:
    path: PurePosixPath
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class SourceFile:
    root: str
    path: PurePosixPath
    language: str
    content: bytes
