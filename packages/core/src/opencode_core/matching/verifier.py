"""Collision-resistant canonical-token span verification."""

from __future__ import annotations

from dataclasses import dataclass

from opencode_core.detection import SimilarityScores
from opencode_core.fingerprinting import K_GRAM_SIZE, FingerprintSet
from opencode_core.normalization import NormalizedToken
from opencode_core.retrieval import Candidate


@dataclass(frozen=True, order=True, slots=True)
class TokenSpan:
    query_start: int
    query_end: int
    candidate_start: int
    candidate_end: int

    @property
    def length(self) -> int:
        return self.query_end - self.query_start


def _canonical(tokens: tuple[NormalizedToken, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((token.kind, token.canonical) for token in tokens)


def _expand(
    query: tuple[tuple[str, str], ...],
    candidate: tuple[tuple[str, str], ...],
    query_position: int,
    candidate_position: int,
) -> TokenSpan | None:
    seed = min(
        K_GRAM_SIZE,
        len(query) - query_position,
        len(candidate) - candidate_position,
    )
    if (
        seed <= 0
        or query[query_position : query_position + seed]
        != candidate[candidate_position : candidate_position + seed]
    ):
        return None
    query_start, candidate_start = query_position, candidate_position
    while (
        query_start > 0
        and candidate_start > 0
        and query[query_start - 1] == candidate[candidate_start - 1]
    ):
        query_start -= 1
        candidate_start -= 1
    query_end = query_position + seed
    candidate_end = candidate_position + seed
    while (
        query_end < len(query)
        and candidate_end < len(candidate)
        and query[query_end] == candidate[candidate_end]
    ):
        query_end += 1
        candidate_end += 1
    return TokenSpan(query_start, query_end, candidate_start, candidate_end)


def _deduplicate(spans: list[TokenSpan]) -> tuple[TokenSpan, ...]:
    ordered = sorted(set(spans), key=lambda span: (-span.length, span))
    retained: list[TokenSpan] = []
    for span in ordered:
        contained = any(
            existing.query_start <= span.query_start
            and existing.query_end >= span.query_end
            and existing.candidate_start <= span.candidate_start
            and existing.candidate_end >= span.candidate_end
            for existing in retained
        )
        if not contained:
            retained.append(span)
    return tuple(sorted(retained))


def verify_candidate(
    query_tokens: tuple[NormalizedToken, ...],
    candidate_tokens: tuple[NormalizedToken, ...],
    candidate: Candidate,
    minimum_tokens: int = 28,
) -> tuple[TokenSpan, ...]:
    query_values = _canonical(query_tokens)
    candidate_values = _canonical(candidate_tokens)
    if candidate.small:
        if query_values == candidate_values and query_values:
            return (TokenSpan(0, len(query_values), 0, len(candidate_values)),)
        return ()
    spans = []
    for evidence in candidate.positions:
        span = _expand(
            query_values,
            candidate_values,
            evidence.query_position,
            evidence.candidate_position,
        )
        if span is not None and span.length >= minimum_tokens:
            spans.append(span)
    return _deduplicate(spans)


def score_span(
    span: TokenSpan,
    query_count: int,
    candidate_count: int,
    query_fingerprints: FingerprintSet,
    candidate_fingerprints: FingerprintSet,
) -> SimilarityScores:
    left = {item.hash_u64 for item in query_fingerprints.fingerprints}
    right = {item.hash_u64 for item in candidate_fingerprints.fingerprints}
    union = left | right
    matched = span.length
    token_union = query_count + candidate_count - matched
    return SimilarityScores(
        fingerprint_jaccard=len(left & right) / len(union) if union else None,
        query_coverage=matched / query_count,
        candidate_coverage=matched / candidate_count,
        token_jaccard=matched / token_union,
    )
