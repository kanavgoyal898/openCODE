"""AST-feature MinHash retrieval with bounded structural/token verification."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from opencode_core.detection import (
    CloneCategory,
    DetectionResult,
    DetectorConfig,
    MatchEvidence,
    SimilarityScores,
    SourceRange,
)
from opencode_core.matching.store import FragmentRecord, InMemoryFragmentStore
from opencode_core.normalization import NormalizedToken
from opencode_core.version import NORMALIZATION_VERSION

STRUCTURAL_VERSION = "struct-v1"
_SIGNATURE_SIZE = 32
_BAND_SIZE = 4


def _features(record: FragmentRecord) -> tuple[str, ...]:
    base = [f"{node.kind}:{min(node.depth, 8)}" for node in record.structural_nodes]
    return tuple("/".join(base[index : index + 3]) for index in range(max(1, len(base) - 2)))


def _hash(feature: str, seed: int) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}\0{feature}".encode()).digest()[:8], "big")


def _signature(record: FragmentRecord) -> tuple[int, ...]:
    features = _features(record) or ("EMPTY",)
    return tuple(
        min(_hash(feature, seed) for feature in features) for seed in range(_SIGNATURE_SIZE)
    )


def _structural_similarity(left: FragmentRecord, right: FragmentRecord) -> float:
    a = [node.kind for node in left.structural_nodes]
    b = [node.kind for node in right.structural_nodes]
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _token_alignment(left: FragmentRecord, right: FragmentRecord) -> tuple[float, int]:
    a = [(token.kind, token.canonical) for token in left.renamed_tokens]
    b = [(token.kind, token.canonical) for token in right.renamed_tokens]
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    blocks = matcher.get_matching_blocks()
    matched = sum(block.size for block in blocks)
    lines = {
        left.renamed_tokens[block.a + offset].source.start_line
        for block in blocks
        for offset in range(block.size)
    }
    coverage = min(matched / len(a), matched / len(b)) if a and b else 0.0
    return coverage, len(lines)


def _range(record: FragmentRecord) -> SourceRange:
    tokens = record.exact_tokens
    first, last = tokens[0].source, tokens[-1].source
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


def _lexically_equal(left: FragmentRecord, right: FragmentRecord) -> bool:
    return tuple((item.kind, item.canonical) for item in left.renamed_tokens) == tuple(
        (item.kind, item.canonical) for item in right.renamed_tokens
    )


def _statements(record: FragmentRecord) -> list[tuple[tuple[str, ...], str | None, set[str]]]:
    by_line: dict[int, list[NormalizedToken]] = defaultdict(list)
    for token in record.exact_tokens:
        by_line[token.source.start_line].append(token)
    statements = []
    for tokens in by_line.values():
        if tokens and tokens[0].canonical in {"def", "function"}:
            continue
        equals = next((index for index, token in enumerate(tokens) if token.canonical == "="), None)
        if equals is None:
            continue
        identifiers = [token.canonical for token in tokens if token.kind == "identifier"]
        defined = next(
            (token.canonical for token in tokens[:equals] if token.kind == "identifier"), None
        )
        used = set(identifiers)
        if defined is not None:
            used.discard(defined)
        shape = tuple(
            "DEF"
            if token.kind == "identifier" and index < equals
            else f"{token.kind}:{token.canonical}"
            for index, token in enumerate(tokens)
        )
        statements.append((shape, defined, used))
    return statements


def _reorder_state(left: FragmentRecord, right: FragmentRecord) -> str | None:
    a, b = _statements(left), _statements(right)
    shapes_a, shapes_b = [item[0] for item in a], [item[0] for item in b]
    if shapes_a == shapes_b or sorted(shapes_a) != sorted(shapes_b):
        return None
    positions = {shape: index for index, shape in enumerate(shapes_b)}
    moved = [item for index, item in enumerate(a) if positions.get(item[0]) != index]
    for index, (_, defined, used) in enumerate(moved):
        if defined is None:
            continue
        for _, other_defined, other_used in moved[index + 1 :]:
            if defined in other_used or (other_defined is not None and other_defined in used):
                return "dependent"
    return "independent"


@dataclass(slots=True)
class StructuralCloneDetector:
    store: InMemoryFragmentStore
    records: tuple[FragmentRecord, ...]
    config: DetectorConfig = field(default_factory=DetectorConfig)
    detector_id: str = "structural-clone-detector"
    category: CloneCategory = "type3"
    algorithm_version: str = STRUCTURAL_VERSION
    _signatures: dict[str, tuple[int, ...]] = field(init=False, repr=False)
    _bands: dict[tuple[int, tuple[int, ...]], set[str]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._signatures = {record.fragment_id: _signature(record) for record in self.records}
        bands: dict[tuple[int, tuple[int, ...]], set[str]] = defaultdict(set)
        for fragment_id, signature in self._signatures.items():
            for index in range(0, _SIGNATURE_SIZE, _BAND_SIZE):
                bands[(index, signature[index : index + _BAND_SIZE])].add(fragment_id)
        self._bands = bands

    def detect(self, query_fragment_id: str) -> tuple[DetectionResult, ...]:
        query = self.store.get_by_fragment_id(query_fragment_id)
        signature = self._signatures[query_fragment_id]
        candidate_ids: set[str] = set()
        for index in range(0, _SIGNATURE_SIZE, _BAND_SIZE):
            candidate_ids.update(
                self._bands.get((index, signature[index : index + _BAND_SIZE]), ())
            )
        ranked = sorted(
            self.records,
            key=lambda item: sum(
                left == right
                for left, right in zip(signature, self._signatures[item.fragment_id], strict=True)
            ),
            reverse=True,
        )
        candidate_ids.update(item.fragment_id for item in ranked[: self.config.retrieval_budget])
        results: list[DetectionResult] = []
        for candidate_id in sorted(candidate_ids - {query_fragment_id}):
            candidate = self.store.get_by_fragment_id(candidate_id)
            if (
                _lexically_equal(query, candidate)
                or not query.exact_tokens
                or not candidate.exact_tokens
            ):
                continue
            structure = _structural_similarity(query, candidate)
            alignment, statements = _token_alignment(query, candidate)
            reorder = _reorder_state(query, candidate)
            if reorder == "dependent":
                structure *= 0.75
            if (
                structure < self.config.structural_threshold
                or alignment < self.config.alignment_threshold
                or statements < self.config.minimum_matched_statements
            ):
                continue
            explanation = [
                "AST_MINHASH_LSH_CANDIDATE",
                "AST_SEQUENCE_ALIGNMENT",
                "RENAMED_TOKEN_LOCAL_ALIGNMENT",
            ]
            if reorder == "independent":
                explanation.append("INDEPENDENT_STATEMENT_REORDER")
            results.append(
                DetectionResult(
                    "type3",
                    "verified",
                    self.detector_id,
                    self.algorithm_version,
                    NORMALIZATION_VERSION,
                    _range(query),
                    _range(candidate),
                    SimilarityScores(None, alignment, alignment, alignment, structure, alignment),
                    MatchEvidence(
                        (),
                        0,
                        len(query.renamed_tokens),
                        0,
                        len(candidate.renamed_tokens),
                        tuple(explanation),
                    ),
                    ("STRUCTURAL_EVIDENCE_NOT_SEMANTIC_EQUIVALENCE", "NOT_PLAGIARISM_PROOF"),
                )
            )
        return tuple(results)
