"""Verified Type 1 and Type 2 detector implementations."""

from __future__ import annotations

from dataclasses import dataclass

from opencode_core.detection import (
    CloneCategory,
    DetectionResult,
    DetectorConfig,
    MatchEvidence,
    SourceRange,
)
from opencode_core.fingerprinting import FingerprintSet
from opencode_core.matching.store import FragmentRecord, InMemoryFragmentStore
from opencode_core.matching.verifier import TokenSpan, score_span, verify_candidate
from opencode_core.normalization import Mode, NormalizedToken
from opencode_core.retrieval import CandidateRetriever
from opencode_core.version import FINGERPRINT_VERSION, NORMALIZATION_VERSION


def _source_range(
    record: FragmentRecord, tokens: tuple[NormalizedToken, ...], span: TokenSpan
) -> SourceRange:
    first = tokens[span.query_start].source
    last = tokens[span.query_end - 1].source
    return SourceRange(
        record.repository_id,
        record.revision_id,
        record.fragment_id,
        first.start_byte,
        last.end_byte,
        first.start_line,
        first.start_column,
        last.end_line,
        last.end_column,
    )


@dataclass(slots=True)
class _LexicalDetector:
    retriever: CandidateRetriever
    store: InMemoryFragmentStore
    config: DetectorConfig
    mode: Mode
    category: CloneCategory
    detector_id: str
    algorithm_version: str = FINGERPRINT_VERSION

    def detect(self, query_fragment_id: str) -> tuple[DetectionResult, ...]:
        query = self.store.get_by_fragment_id(query_fragment_id)
        query_tokens, query_fingerprints = self._stream(query)
        retrieval = self.retriever.retrieve(
            query_fingerprints,
            excluded_fragments=((query.repository_id, query.revision_id, query.fragment_id),),
        )
        results: list[DetectionResult] = []
        for candidate in retrieval.candidates:
            record = self.store.get(
                candidate.repository_id,
                candidate.revision_id,
                candidate.fragment_id,
            )
            candidate_tokens, candidate_fingerprints = self._stream(record)
            for span in verify_candidate(
                query_tokens,
                candidate_tokens,
                candidate,
                self.config.minimum_tokens,
            ):
                if self.category == "type2" and self._exact_equal(query, record, span):
                    continue
                candidate_span = TokenSpan(
                    span.candidate_start,
                    span.candidate_end,
                    span.query_start,
                    span.query_end,
                )
                results.append(
                    DetectionResult(
                        category=self.category,
                        evidence_state="verified",
                        detector_id=self.detector_id,
                        algorithm_version=self.algorithm_version,
                        normalization_version=NORMALIZATION_VERSION,
                        left=_source_range(query, query_tokens, span),
                        right=_source_range(record, candidate_tokens, candidate_span),
                        scores=score_span(
                            span,
                            len(query_tokens),
                            len(candidate_tokens),
                            query_fingerprints,
                            candidate_fingerprints,
                        ),
                        evidence=MatchEvidence(
                            candidate.shared_hashes,
                            span.query_start,
                            span.query_end,
                            span.candidate_start,
                            span.candidate_end,
                            ("CANONICAL_TOKEN_EQUALITY", "POSITIONAL_SEED_EXPANSION"),
                        ),
                        limitations=("LEXICAL_EVIDENCE_ONLY", "NOT_PLAGIARISM_PROOF"),
                    )
                )
        return tuple(
            sorted(
                results,
                key=lambda result: (
                    result.right.repository_id,
                    result.right.revision_id,
                    result.right.fragment_id,
                    result.left.start_byte,
                    result.right.start_byte,
                ),
            )
        )

    def _stream(self, record: FragmentRecord) -> tuple[tuple[NormalizedToken, ...], FingerprintSet]:
        if self.mode == "exact":
            return record.exact_tokens, record.exact_fingerprints
        return record.renamed_tokens, record.renamed_fingerprints

    @staticmethod
    def _exact_equal(query: FragmentRecord, candidate: FragmentRecord, span: TokenSpan) -> bool:
        left = query.exact_tokens[span.query_start : span.query_end]
        right = candidate.exact_tokens[span.candidate_start : span.candidate_end]
        return tuple((token.kind, token.canonical) for token in left) == tuple(
            (token.kind, token.canonical) for token in right
        )


class ExactCloneDetector(_LexicalDetector):
    def __init__(
        self,
        retriever: CandidateRetriever,
        store: InMemoryFragmentStore,
        config: DetectorConfig | None = None,
    ) -> None:
        super().__init__(
            retriever,
            store,
            DetectorConfig() if config is None else config,
            "exact",
            "type1",
            "exact-clone-detector",
        )


class TokenCloneDetector(_LexicalDetector):
    def __init__(
        self,
        retriever: CandidateRetriever,
        store: InMemoryFragmentStore,
        config: DetectorConfig | None = None,
    ) -> None:
        super().__init__(
            retriever,
            store,
            DetectorConfig() if config is None else config,
            "renamed",
            "type2",
            "token-clone-detector",
        )
