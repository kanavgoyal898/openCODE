from __future__ import annotations

from pathlib import Path

from opencode_core.detection import CloneDetector, DetectorConfig
from opencode_core.engine import AnalysisWorkspace, analyze_directory, find_clones
from opencode_core.semantic import (
    BehavioralSandbox,
    HashCodeEmbeddingModel,
    SemanticCloneDetector,
)

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


def test_multi_evidence_policy_promotes_cross_language_candidate(tmp_path: Path) -> None:
    (tmp_path / "sum.py").write_text(LOOP)
    (tmp_path / "sum.js").write_text(
        "function sumValues(numbers) {\n"
        "  let total = 0;\n"
        "  for (const number of numbers) { total = total + number; }\n"
        "  return total;\n}\n"
    )
    workspace = analyze_directory(tmp_path)
    detector = SemanticCloneDetector(
        workspace.store,
        workspace.records,
        DetectorConfig(semantic_verification=True),
    )

    result = detector.detect("sum.py")[0]

    assert result.evidence_state == "verified"
    assert result.algorithm_version.startswith("semantic-v2:")
    assert result.scores.cfg_similarity == 1
    assert result.scores.data_flow_similarity == 1
    assert "PDG_FEATURE_AGREEMENT" in result.evidence.explanation_codes
    assert "EMBEDDING_SIMILARITY_IS_NOT_SEMANTIC_EQUIVALENCE" in result.limitations


def test_unsupported_dynamic_construct_stays_candidate(tmp_path: Path) -> None:
    (tmp_path / "left.py").write_text("def calculate(text):\n    return eval(text)\n")
    (tmp_path / "right.py").write_text("def calculate(code):\n    return eval(code)\n")
    workspace = analyze_directory(tmp_path)
    detector = SemanticCloneDetector(
        workspace.store,
        workspace.records,
        DetectorConfig(semantic_threshold=0, semantic_verification=True),
    )

    result = detector.detect("left.py")[0]

    assert result.evidence_state == "candidate"
    assert "UNSUPPORTED_DYNAMIC_OR_IO_CONSTRUCT" in result.limitations


def test_behavioral_sandbox_requires_authorization_and_isolation() -> None:
    assert BehavioralSandbox().run_approved_harness("print(1)").status == "disabled"
    assert (
        BehavioralSandbox(enabled=True).run_approved_harness("print(1)").status
        == "isolation_required"
    )


def test_behavioral_sandbox_bounds_approved_harness() -> None:
    sandbox = BehavioralSandbox(enabled=True, network_isolated=True, timeout_seconds=0.1)
    completed = sandbox.run_approved_harness("print('domain-ok')")
    assert (completed.status, completed.exit_code, completed.stdout.strip()) == (
        "completed",
        0,
        "domain-ok",
    )
    assert sandbox.run_approved_harness("while True: pass").status == "timeout"
