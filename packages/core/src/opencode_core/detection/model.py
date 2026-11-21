"""Versioned result types shared by independent detection engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

CloneCategory = Literal["type1", "type2", "type3", "type4"]
EvidenceState = Literal["verified", "candidate", "rejected"]


@dataclass(frozen=True, slots=True)
class DetectorConfig:
    minimum_tokens: int = 28
    merge_gap: int = 3
    structural_threshold: float = 0.80
    alignment_threshold: float = 0.65
    minimum_matched_statements: int = 3
    retrieval_budget: int = 100
    semantic_threshold: float = 0.28
    semantic_top_k: int = 20
    semantic_verification: bool = False
    program_analysis_threshold: float = 0.70

    def __post_init__(self) -> None:
        if (
            self.minimum_tokens <= 0
            or self.merge_gap < 0
            or not 0 <= self.structural_threshold <= 1
            or not 0 <= self.alignment_threshold <= 1
            or self.minimum_matched_statements <= 0
            or self.retrieval_budget <= 0
            or not 0 <= self.semantic_threshold <= 1
            or self.semantic_top_k <= 0
            or not 0 <= self.program_analysis_threshold <= 1
        ):
            raise ValueError("detector thresholds must be non-negative")


@dataclass(frozen=True, order=True, slots=True)
class SourceRange:
    repository_id: str
    revision_id: str
    fragment_id: str
    start_byte: int
    end_byte: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True, slots=True)
class SimilarityScores:
    fingerprint_jaccard: float | None
    query_coverage: float
    candidate_coverage: float
    token_jaccard: float
    structural_similarity: float | None = None
    aligned_token_similarity: float | None = None
    embedding_cosine: float | None = None
    cfg_similarity: float | None = None
    data_flow_similarity: float | None = None
    pdg_similarity: float | None = None
    confidence: None = None


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    shared_hashes: tuple[int, ...]
    query_token_start: int
    query_token_end: int
    candidate_token_start: int
    candidate_token_end: int
    explanation_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DetectionResult:
    category: CloneCategory
    evidence_state: EvidenceState
    detector_id: str
    algorithm_version: str
    normalization_version: str
    left: SourceRange
    right: SourceRange
    scores: SimilarityScores
    evidence: MatchEvidence
    limitations: tuple[str, ...]


class CloneDetector(Protocol):
    detector_id: str
    category: CloneCategory
    algorithm_version: str

    def detect(self, query_fragment_id: str) -> tuple[DetectionResult, ...]: ...
