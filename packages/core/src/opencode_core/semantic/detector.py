"""Versioned code embeddings and exact-cosine candidate retrieval."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Protocol

from opencode_core.detection import (
    CloneCategory,
    DetectionResult,
    DetectorConfig,
    MatchEvidence,
    SimilarityScores,
    SourceRange,
)
from opencode_core.matching.store import FragmentRecord, InMemoryFragmentStore
from opencode_core.semantic.analysis import compare_program_evidence
from opencode_core.version import NORMALIZATION_VERSION

SEMANTIC_VERSION = "semantic-v1"
MODEL_ID = "opencode/feature-hash-code-embedding-v1"
MODEL_CHECKSUM = "sha256:cee9361b941ac964799b2c9a86fe69c3bf0e5707bfb6f5a5239adbd006b34fc8"
_WORDS = re.compile(r"[A-Za-z][a-z]*|[A-Z]+(?![a-z])|\d+")


class CodeEmbeddingModel(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def checksum(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    @property
    def max_tokens(self) -> int: ...

    def embed(self, record: FragmentRecord) -> tuple[tuple[float, ...], bool]: ...


def _features(record: FragmentRecord, maximum: int) -> tuple[list[str], bool]:
    tokens = record.exact_tokens[:maximum]
    features: list[str] = []
    for token in tokens:
        features.append(f"kind:{token.kind}")
        if token.kind in {"keyword", "operator", "other"}:
            features.append(f"syntax:{token.canonical.casefold()}")
        if token.kind == "identifier":
            words = _WORDS.findall(token.canonical.replace("_", " "))
            for word in words:
                features.extend([f"word:{word.casefold()}"] * 4)
    features.extend(f"ast:{node.kind}" for node in record.structural_nodes)
    return features, len(record.exact_tokens) > maximum


@dataclass(frozen=True, slots=True)
class HashCodeEmbeddingModel:
    """Offline deterministic baseline; not a pretrained neural model."""

    model_id: str = MODEL_ID
    checksum: str = MODEL_CHECKSUM
    dimensions: int = 256
    max_tokens: int = 2048

    def embed(self, record: FragmentRecord) -> tuple[tuple[float, ...], bool]:
        features, truncated = _features(record, self.max_tokens)
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.sha256(feature.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return tuple(value / norm for value in vector), truncated


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _range(record: FragmentRecord) -> SourceRange:
    first, last = record.exact_tokens[0].source, record.exact_tokens[-1].source
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
class SemanticCloneDetector:
    store: InMemoryFragmentStore
    records: tuple[FragmentRecord, ...]
    config: DetectorConfig = field(default_factory=DetectorConfig)
    model: CodeEmbeddingModel = field(default_factory=HashCodeEmbeddingModel)
    detector_id: str = "semantic-clone-detector"
    category: CloneCategory = "type4"
    algorithm_version: str = SEMANTIC_VERSION
    _vectors: dict[str, tuple[tuple[float, ...], bool]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._vectors = {record.fragment_id: self.model.embed(record) for record in self.records}

    def detect(self, query_fragment_id: str) -> tuple[DetectionResult, ...]:
        query = self.store.get_by_fragment_id(query_fragment_id)
        vector, query_truncated = self._vectors[query_fragment_id]
        ranked = sorted(
            (
                (_cosine(vector, candidate_vector), fragment_id, truncated)
                for fragment_id, (candidate_vector, truncated) in self._vectors.items()
                if fragment_id != query_fragment_id
            ),
            key=lambda item: (-item[0], item[1]),
        )[: self.config.semantic_top_k]
        results = []
        for cosine, fragment_id, candidate_truncated in ranked:
            if cosine < self.config.semantic_threshold:
                continue
            candidate = self.store.get_by_fragment_id(fragment_id)
            program = compare_program_evidence(query, candidate)
            verified = (
                self.config.semantic_verification
                and program.supported
                and program.cfg_similarity >= self.config.program_analysis_threshold
                and program.data_flow_similarity >= self.config.program_analysis_threshold
                and program.pdg_similarity >= self.config.program_analysis_threshold
            )
            limitations = [
                "EMBEDDING_SIMILARITY_IS_NOT_SEMANTIC_EQUIVALENCE",
                "NOT_PLAGIARISM_PROOF",
            ]
            if not verified:
                limitations.append("CANDIDATE_REQUIRES_MULTI_EVIDENCE_VERIFICATION")
            if not program.supported:
                limitations.append("UNSUPPORTED_DYNAMIC_OR_IO_CONSTRUCT")
            if query_truncated or candidate_truncated:
                limitations.append("EMBEDDING_INPUT_TRUNCATED")
            results.append(
                DetectionResult(
                    "type4",
                    "verified" if verified else "candidate",
                    self.detector_id,
                    f"{'semantic-v2' if verified else self.algorithm_version}:"
                    f"{self.model.model_id}:{self.model.checksum}",
                    NORMALIZATION_VERSION,
                    _range(query),
                    _range(candidate),
                    SimilarityScores(
                        None,
                        0.0,
                        0.0,
                        0.0,
                        embedding_cosine=cosine,
                        cfg_similarity=program.cfg_similarity,
                        data_flow_similarity=program.data_flow_similarity,
                        pdg_similarity=program.pdg_similarity,
                    ),
                    MatchEvidence(
                        (),
                        0,
                        len(query.renamed_tokens),
                        0,
                        len(candidate.renamed_tokens),
                        (
                            "CODE_EMBEDDING_COSINE_CANDIDATE",
                            "EXACT_VECTOR_SEARCH",
                            *(
                                (
                                    "CFG_SHAPE_AGREEMENT",
                                    "DEF_USE_GRAPH_AGREEMENT",
                                    "PDG_FEATURE_AGREEMENT",
                                )
                                if verified
                                else ()
                            ),
                        ),
                    ),
                    tuple(limitations),
                )
            )
        return tuple(results)
