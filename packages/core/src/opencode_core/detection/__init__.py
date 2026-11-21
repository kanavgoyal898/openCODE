"""Common clone detector and unified result contracts."""

from opencode_core.detection.model import (
    CloneCategory,
    CloneDetector,
    DetectionResult,
    DetectorConfig,
    EvidenceState,
    MatchEvidence,
    SimilarityScores,
    SourceRange,
)

__all__ = [
    "CloneCategory",
    "CloneDetector",
    "DetectionResult",
    "DetectorConfig",
    "EvidenceState",
    "MatchEvidence",
    "SimilarityScores",
    "SourceRange",
]
