"""Standalone orchestration used by CLI and future application adapters."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from opencode_core.detection import CloneDetector, DetectionResult, DetectorConfig
from opencode_core.fingerprinting import fingerprint
from opencode_core.indexing import (
    FragmentFingerprintSet,
    InMemoryFingerprintIndex,
    RevisionFingerprintSet,
)
from opencode_core.matching import (
    ExactCloneDetector,
    FragmentRecord,
    InMemoryFragmentStore,
    TokenCloneDetector,
)
from opencode_core.normalization import normalize
from opencode_core.parsers import Diagnostic, SourceScanner, default_registry
from opencode_core.retrieval import CandidateRetriever
from opencode_core.semantic import SemanticCloneDetector
from opencode_core.structural import StructuralCloneDetector


@dataclass(frozen=True, slots=True)
class AnalysisWorkspace:
    repository_id: str
    root: Path
    records: tuple[FragmentRecord, ...]
    diagnostics: tuple[Diagnostic, ...]
    index: InMemoryFingerprintIndex
    store: InMemoryFragmentStore


def _repository_id(root: Path, files: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256(b"opencode-repository-v1\0")
    for path, content in sorted(files):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def _record(
    repository_id: str,
    fragment_id: str,
    language: str,
    content: bytes,
) -> FragmentRecord:
    adapter = default_registry().detect(fragment_id, explicit=language)
    parsed = adapter.tokenize(content)
    exact = normalize(parsed.tokens, "exact")
    renamed = normalize(parsed.tokens, "renamed")
    revision = hashlib.sha256(fragment_id.encode() + b"\0" + content).hexdigest()
    return FragmentRecord(
        repository_id,
        revision,
        fragment_id,
        exact,
        renamed,
        fingerprint(exact, "exact"),
        fingerprint(renamed, "renamed"),
        parsed.structural_nodes,
    )


def analyze_directory(
    root: Path,
    exclude_patterns: tuple[str, ...] = (),
) -> AnalysisWorkspace:
    resolved = root.resolve(strict=True)
    scanner = SourceScanner(default_registry(), exclude_patterns=exclude_patterns)
    files = list(scanner.scan(resolved))
    repository_id = _repository_id(resolved, [(str(item.path), item.content) for item in files])
    records: list[FragmentRecord] = []
    diagnostics = list(scanner.diagnostics)
    for source in files:
        try:
            records.append(
                _record(repository_id, str(source.path), source.language, source.content)
            )
        except ValueError as error:
            diagnostics.append(
                Diagnostic(source.path, getattr(error, "code", "ANALYSIS_ERROR"), str(error))
            )
    store = InMemoryFragmentStore()
    index = InMemoryFingerprintIndex()
    for record in records:
        store.put(record)
        index.replace_revision(
            RevisionFingerprintSet(
                record.repository_id,
                record.revision_id,
                (
                    FragmentFingerprintSet(record.fragment_id, record.exact_fingerprints),
                    FragmentFingerprintSet(record.fragment_id, record.renamed_fingerprints),
                ),
            )
        )
    return AnalysisWorkspace(
        repository_id,
        resolved,
        tuple(sorted(records, key=lambda item: item.fragment_id)),
        tuple(diagnostics),
        index,
        store,
    )


def find_clones(
    workspace: AnalysisWorkspace,
    categories: tuple[str, ...] = ("type1", "type2"),
    minimum_tokens: int = 28,
    detector_config: DetectorConfig | None = None,
) -> tuple[DetectionResult, ...]:
    retriever = CandidateRetriever(workspace.index)
    config = (
        DetectorConfig(minimum_tokens=minimum_tokens)
        if detector_config is None
        else detector_config
    )
    detectors: list[CloneDetector] = []
    if "type1" in categories:
        detectors.append(ExactCloneDetector(retriever, workspace.store, config))
    if "type2" in categories:
        detectors.append(TokenCloneDetector(retriever, workspace.store, config))
    if "type3" in categories:
        detectors.append(StructuralCloneDetector(workspace.store, workspace.records, config))
    if "type4" in categories:
        detectors.append(SemanticCloneDetector(workspace.store, workspace.records, config))
    unique: dict[tuple[object, ...], DetectionResult] = {}
    for record in workspace.records:
        for detector in detectors:
            for result in detector.detect(record.fragment_id):
                endpoints = sorted(
                    (
                        (
                            result.left.repository_id,
                            result.left.revision_id,
                            result.left.fragment_id,
                        ),
                        (
                            result.right.repository_id,
                            result.right.revision_id,
                            result.right.fragment_id,
                        ),
                    )
                )
                key = (
                    result.category,
                    *endpoints,
                    min(result.left.start_byte, result.right.start_byte),
                    max(result.left.end_byte, result.right.end_byte),
                )
                unique[key] = result
    return tuple(
        sorted(
            unique.values(),
            key=lambda result: (
                result.category,
                result.left.fragment_id,
                result.right.fragment_id,
                result.left.start_byte,
            ),
        )
    )


def compare_files(left: Path, right: Path) -> tuple[DetectionResult, ...]:
    left_bytes = left.read_bytes()
    right_bytes = right.read_bytes()
    registry = default_registry()
    left_adapter = registry.detect(left.name, prefix=left_bytes[:256])
    right_adapter = registry.detect(right.name, prefix=right_bytes[:256])
    records = (
        _record("compare-left", f"left/{left.name}", left_adapter.language, left_bytes),
        _record("compare-right", f"right/{right.name}", right_adapter.language, right_bytes),
    )
    store = InMemoryFragmentStore()
    index = InMemoryFingerprintIndex()
    for record in records:
        store.put(record)
        index.replace_revision(
            RevisionFingerprintSet(
                record.repository_id,
                record.revision_id,
                (
                    FragmentFingerprintSet(record.fragment_id, record.exact_fingerprints),
                    FragmentFingerprintSet(record.fragment_id, record.renamed_fingerprints),
                ),
            )
        )
    workspace = AnalysisWorkspace("compare", Path.cwd(), records, (), index, store)
    return find_clones(workspace)
