"""Validated, dependency-free settings shared by standalone engine adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from os import environ

DEFAULT_MAX_FILE_BYTES = 2_000_000
DEFAULT_MAX_DIRECTORY_DEPTH = 32
DEFAULT_MAX_FILES = 100_000


class ConfigurationError(ValueError):
    """Raised when a setting cannot be safely interpreted."""


def _positive_integer(values: Mapping[str, str], name: str, default: int) -> int:
    raw = values.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be an integer") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True, slots=True)
class CoreSettings:
    """Resource boundaries that can be used without service dependencies."""

    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES
    max_directory_depth: int = DEFAULT_MAX_DIRECTORY_DEPTH
    max_files: int = DEFAULT_MAX_FILES

    @classmethod
    def from_environment(cls, values: Mapping[str, str] | None = None) -> CoreSettings:
        source = environ if values is None else values
        return cls(
            max_file_bytes=_positive_integer(
                source, "OPENCODE_MAX_FILE_BYTES", DEFAULT_MAX_FILE_BYTES
            ),
            max_directory_depth=_positive_integer(
                source, "OPENCODE_MAX_DIRECTORY_DEPTH", DEFAULT_MAX_DIRECTORY_DEPTH
            ),
            max_files=_positive_integer(source, "OPENCODE_MAX_FILES", DEFAULT_MAX_FILES),
        )
