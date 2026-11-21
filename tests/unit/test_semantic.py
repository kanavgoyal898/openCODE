from __future__ import annotations

from pathlib import Path

from opencode_core.detection import CloneDetector, DetectorConfig
from opencode_core.engine import AnalysisWorkspace, analyze_directory, find_clones
from opencode_core.semantic import HashCodeEmbeddingModel, SemanticCloneDetector

LOOP = """def sum_values(numbers):
    total = 0
    for number in numbers:
        total = total + number
    return total
"""

BUILTIN = """def calculate_sum(items):
    return sum(items)
"""


def _workspace(tmp_path: Path) -> AnalysisWorkspace:
    (tmp_path / "loop.py").write_text(LOOP)
    (tmp_path / "builtin.py").write_text(BUILTIN)
    (tmp_path / "negative.py").write_text(
        "def format_name(first, last):\n    return f'{last}, {first}'\n"
    )
    return analyze_directory(tmp_path)


def test_embedding_is_deterministic_and_versioned(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    model = HashCodeEmbeddingModel()
    record = workspace.store.get_by_fragment_id("loop.py")

    assert model.embed(record) == model.embed(record)
    assert model.model_id == "opencode/feature-hash-code-embedding-v1"
    assert model.checksum.startswith("sha256:")


def test_semantic_detector_returns_candidate_never_equivalence(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    detector: CloneDetector = SemanticCloneDetector(
        workspace.store,
        workspace.records,
        DetectorConfig(semantic_threshold=0.15),
    )

    results = detector.detect("loop.py")
    match = next(item for item in results if item.right.fragment_id == "builtin.py")

    assert match.category == "type4"
    assert match.evidence_state == "candidate"
    assert match.scores.embedding_cosine is not None
    assert "EMBEDDING_SIMILARITY_IS_NOT_SEMANTIC_EQUIVALENCE" in match.limitations
    assert match.detector_id == "semantic-clone-detector"


def test_engine_deduplicates_symmetric_semantic_candidates(tmp_path: Path) -> None:
    results = find_clones(_workspace(tmp_path), ("type4",))
    pairs = [tuple(sorted((item.left.fragment_id, item.right.fragment_id))) for item in results]
    assert len(pairs) == len(set(pairs))
    assert all(item.evidence_state == "candidate" for item in results)


def test_embedding_truncation_is_disclosed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    detector = SemanticCloneDetector(
        workspace.store,
        workspace.records,
        DetectorConfig(semantic_threshold=0),
        HashCodeEmbeddingModel(max_tokens=1),
    )
    assert any(
        "EMBEDDING_INPUT_TRUNCATED" in item.limitations for item in detector.detect("loop.py")
    )
