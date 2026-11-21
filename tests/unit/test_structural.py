from __future__ import annotations

from pathlib import Path

from opencode_core.detection import CloneDetector
from opencode_core.engine import AnalysisWorkspace, analyze_directory, find_clones
from opencode_core.structural import StructuralCloneDetector

BASE = """def summarize(values):
    count = len(values)
    total = sum(values)
    average = total / count
    adjusted = average * 2
    label = "summary"
    result = {label: adjusted, "count": count}
    return result
"""

NEAR_MISS = """def summarize(items):
    count = len(items)
    total = sum(items)
    average = total / count
    adjusted = average * 3
    adjusted = adjusted + 1
    label = "result"
    result = {label: adjusted, "count": count}
    return result
"""


def _workspace(tmp_path: Path, right: str = NEAR_MISS) -> AnalysisWorkspace:
    (tmp_path / "base.py").write_text(BASE)
    (tmp_path / "near.py").write_text(right)
    return analyze_directory(tmp_path)


def test_structural_detector_common_interface_and_type3_evidence(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    detector: CloneDetector = StructuralCloneDetector(workspace.store, workspace.records)

    results = detector.detect("base.py")

    assert results
    result = results[0]
    assert result.category == "type3"
    assert result.evidence_state == "verified"
    assert result.scores.structural_similarity is not None
    assert result.scores.aligned_token_similarity is not None
    assert "AST_MINHASH_LSH_CANDIDATE" in result.evidence.explanation_codes
    assert result.algorithm_version == "struct-v1"


def test_engine_deduplicates_symmetric_structural_matches(tmp_path: Path) -> None:
    results = find_clones(_workspace(tmp_path), ("type3",))
    assert len(results) == 1


def test_structural_detector_rejects_unrelated_negative(tmp_path: Path) -> None:
    unrelated = """def greet(name):
    if not name:
        return None
    for character in name:
        print(character)
    return name.upper()
"""
    assert find_clones(_workspace(tmp_path, unrelated), ("type3",)) == ()


def test_independent_reorder_is_explained(tmp_path: Path) -> None:
    left = """def prepare(a, b):
    first = normalize(a)
    second = validate(b)
    third = encode(first)
    fourth = render(second)
    result = combine(third, fourth)
    return result
"""
    right = """def prepare(a, b):
    second = validate(b)
    first = normalize(a)
    third = encode(first)
    fourth = render(second)
    result = combine(third, fourth)
    return result
"""
    (tmp_path / "base.py").write_text(left)
    (tmp_path / "near.py").write_text(right)
    workspace = analyze_directory(tmp_path)

    result = find_clones(workspace, ("type3",))[0]

    assert "INDEPENDENT_STATEMENT_REORDER" in result.evidence.explanation_codes


def test_dependent_reorder_is_not_credited(tmp_path: Path) -> None:
    left = """def calculate(value):
    first = value + 1
    second = first * 2
    third = second - 3
    fourth = third / 4
    result = fourth + first
    return result
"""
    right = """def calculate(value):
    second = first * 2
    first = value + 1
    third = second - 3
    fourth = third / 4
    result = fourth + first
    return result
"""
    (tmp_path / "base.py").write_text(left)
    (tmp_path / "near.py").write_text(right)

    results = find_clones(analyze_directory(tmp_path), ("type3",))

    assert not results or all(
        "INDEPENDENT_STATEMENT_REORDER" not in item.evidence.explanation_codes for item in results
    )
