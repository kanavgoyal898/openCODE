"""High-recall retrieval; candidates are not verified clone matches."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from opencode_core.fingerprinting import FingerprintSet
from opencode_core.indexing import FingerprintQuery, Posting


class FingerprintIndexView(Protocol):
    def postings(self, query: FingerprintQuery) -> tuple[Posting, ...]: ...

    def document_frequency(self, query: FingerprintQuery) -> int: ...

    def fragment_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    minimum_shared_hashes: int = 3
    stop_floor: int = 500
    stop_ratio: float = 0.01
    max_postings: int = 100_000
    max_candidates: int = 10_000

    def __post_init__(self) -> None:
        if self.minimum_shared_hashes <= 0 or self.stop_floor < 0:
            raise ValueError("retrieval thresholds must be non-negative")
        if not 0 <= self.stop_ratio <= 1:
            raise ValueError("stop ratio must be between zero and one")
        if self.max_postings <= 0 or self.max_candidates <= 0:
            raise ValueError("retrieval budgets must be positive")


@dataclass(frozen=True, order=True, slots=True)
class PositionEvidence:
    hash_u64: int
    query_position: int
    candidate_position: int


@dataclass(frozen=True, slots=True)
class Candidate:
    repository_id: str
    revision_id: str
    fragment_id: str
    shared_hashes: tuple[int, ...]
    positions: tuple[PositionEvidence, ...]
    small: bool


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    candidates: tuple[Candidate, ...]
    stop_hashes: tuple[int, ...]
    postings_examined: int
    truncated: bool


class CandidateRetriever:
    def __init__(
        self,
        index: FingerprintIndexView,
        policy: RetrievalPolicy | None = None,
    ) -> None:
        self.index = index
        self.policy = RetrievalPolicy() if policy is None else policy

    def retrieve(
        self,
        query: FingerprintSet,
        excluded_fragments: Iterable[tuple[str, str, str]] = (),
    ) -> RetrievalResult:
        excluded = frozenset(excluded_fragments)
        fragment_total = self.index.fragment_count()
        stop_threshold = max(self.policy.stop_floor, int(self.policy.stop_ratio * fragment_total))
        hashes: dict[tuple[str, str, str], set[int]] = {}
        positions: dict[tuple[str, str, str], set[PositionEvidence]] = {}
        small_candidates: set[tuple[str, str, str]] = set()
        stop_hashes: set[int] = set()
        examined = 0
        truncated = False

        for selected in query.fingerprints:
            index_query = FingerprintQuery(
                query.algorithm_version,
                query.normalization_version,
                query.mode,
                selected.hash_u64,
            )
            if self.index.document_frequency(index_query) > stop_threshold:
                stop_hashes.add(selected.hash_u64)
                continue
            for posting in self.index.postings(index_query):
                if examined >= self.policy.max_postings:
                    truncated = True
                    break
                examined += 1
                identity = (posting.repository_id, posting.revision_id, posting.fragment_id)
                if identity in excluded:
                    continue
                if identity not in hashes and len(hashes) >= self.policy.max_candidates:
                    truncated = True
                    continue
                hashes.setdefault(identity, set()).add(selected.hash_u64)
                positions.setdefault(identity, set()).add(
                    PositionEvidence(
                        selected.hash_u64,
                        selected.token_position,
                        posting.token_position,
                    )
                )
                if selected.small and posting.small:
                    small_candidates.add(identity)
            if truncated and examined >= self.policy.max_postings:
                break

        candidates = []
        for identity, shared in hashes.items():
            small = identity in small_candidates
            if not small and len(shared) < self.policy.minimum_shared_hashes:
                continue
            candidates.append(
                Candidate(
                    *identity,
                    shared_hashes=tuple(sorted(shared)),
                    positions=tuple(sorted(positions[identity])),
                    small=small,
                )
            )
        candidates.sort(
            key=lambda item: (
                -len(item.shared_hashes),
                item.repository_id,
                item.revision_id,
                item.fragment_id,
            )
        )
        return RetrievalResult(
            tuple(candidates),
            tuple(sorted(stop_hashes)),
            examined,
            truncated,
        )
