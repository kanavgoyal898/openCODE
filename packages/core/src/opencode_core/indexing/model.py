"""Framework-neutral records used by fingerprint index adapters."""

from __future__ import annotations

from dataclasses import dataclass

from opencode_core.fingerprinting import FingerprintSet
from opencode_core.normalization import Mode


@dataclass(frozen=True, order=True, slots=True)
class FingerprintKey:
    algorithm_version: str
    normalization_version: str
    mode: Mode
    hash_u64: int


@dataclass(frozen=True, slots=True)
class FingerprintQuery:
    algorithm_version: str
    normalization_version: str
    mode: Mode
    hash_u64: int

    @property
    def key(self) -> FingerprintKey:
        return FingerprintKey(
            self.algorithm_version,
            self.normalization_version,
            self.mode,
            self.hash_u64,
        )


@dataclass(frozen=True, order=True, slots=True)
class Posting:
    repository_id: str
    revision_id: str
    fragment_id: str
    token_position: int
    small: bool


@dataclass(frozen=True, slots=True)
class FragmentFingerprintSet:
    fragment_id: str
    fingerprints: FingerprintSet


@dataclass(frozen=True, slots=True)
class RevisionFingerprintSet:
    repository_id: str
    revision_id: str
    fragments: tuple[FragmentFingerprintSet, ...]

    def __post_init__(self) -> None:
        if not self.repository_id or not self.revision_id:
            raise ValueError("repository and revision identifiers are required")
        fragment_ids = [fragment.fragment_id for fragment in self.fragments]
        if len(fragment_ids) != len(set(fragment_ids)):
            raise ValueError("fragment identifiers must be unique within a revision")
