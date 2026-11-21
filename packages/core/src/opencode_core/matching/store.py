"""Standalone fragment evidence store used before PostgreSQL persistence exists."""

from __future__ import annotations

from dataclasses import dataclass

from opencode_core.fingerprinting import FingerprintSet
from opencode_core.normalization import NormalizedToken
from opencode_core.parsers.model import StructuralNode


@dataclass(frozen=True, slots=True)
class FragmentRecord:
    repository_id: str
    revision_id: str
    fragment_id: str
    exact_tokens: tuple[NormalizedToken, ...]
    renamed_tokens: tuple[NormalizedToken, ...]
    exact_fingerprints: FingerprintSet
    renamed_fingerprints: FingerprintSet
    structural_nodes: tuple[StructuralNode, ...] = ()


class InMemoryFragmentStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], FragmentRecord] = {}

    def put(self, record: FragmentRecord) -> None:
        self._records[(record.repository_id, record.revision_id, record.fragment_id)] = record

    def get(self, repository_id: str, revision_id: str, fragment_id: str) -> FragmentRecord:
        return self._records[(repository_id, revision_id, fragment_id)]

    def get_by_fragment_id(self, fragment_id: str) -> FragmentRecord:
        matches = [record for key, record in self._records.items() if key[2] == fragment_id]
        if len(matches) != 1:
            raise KeyError(f"fragment identifier is missing or ambiguous: {fragment_id}")
        return matches[0]
