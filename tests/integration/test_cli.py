from __future__ import annotations

import json
from pathlib import Path

import pytest
from opencode_cli.main import main


def _clone_source(name: str = "compute", left: str = "left", right: str = "right") -> str:
    return (
        f"def {name}({left}, {right}):\n"
        f"    first = {left} + {right}\n"
        f"    second = first * {left}\n"
        f"    third = second - {right}\n"
        f"    fourth = third / ({left} + 1)\n"
        "    label = 'value'\n"
        "    return fourth, label\n"
    )


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "first.py").write_text(_clone_source(), encoding="utf-8")
    (root / "second.py").write_text(_clone_source(), encoding="utf-8")
    return root


def test_scan_json_has_stable_versioned_shape(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repository(tmp_path)

    assert main(["scan", str(root), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["schemaVersion"] == "1"
    assert report["algorithmVersion"] == "fp-v1"
    assert report["normalizationVersion"] == "norm-v1"
    assert report["result"]["files"] == 2
    assert report["result"]["tokens"] > 50


def test_find_clones_json_and_sarif_report_real_matches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repository(tmp_path)

    assert main(["find-clones", str(root), "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["result"]["matchCount"] == 1
    assert report["result"]["matches"][0]["category"] == "type1"
    assert report["result"]["matches"][0]["evidence_state"] == "verified"

    assert main(["find-clones", str(root), "--format", "sarif"]) == 0
    sarif = json.loads(capsys.readouterr().out)
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["results"][0]["ruleId"] == "opencode-type1"


def test_compare_no_match_is_success_and_renamed_match_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    left = tmp_path / "left.py"
    right = tmp_path / "right.py"
    unrelated = tmp_path / "unrelated.py"
    left.write_text(_clone_source(), encoding="utf-8")
    right.write_text(_clone_source("calculate", "a", "b"), encoding="utf-8")
    unrelated.write_text("def only(items):\n    return len(items)\n", encoding="utf-8")

    assert main(["compare", str(left), str(right), "--mode", "renamed", "--json"]) == 0
    renamed = json.loads(capsys.readouterr().out)
    assert renamed["result"]["matches"][0]["category"] == "type2"

    assert main(["compare", str(left), str(unrelated), "--json"]) == 0
    no_match = json.loads(capsys.readouterr().out)
    assert no_match["result"]["matchCount"] == 0


def test_stats_and_benchmark_emit_observed_results(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repository(tmp_path)
    output = tmp_path / "benchmark.json"

    assert main(["stats", str(root), "--json"]) == 0
    stats = json.loads(capsys.readouterr().out)
    assert stats["result"]["fingerprints"] > 0

    assert main(["benchmark", str(root), "--runs", "1", "--output", str(output), "--json"]) == 0
    benchmark = json.loads(capsys.readouterr().out)
    assert benchmark["result"]["observed"] is True
    assert benchmark["result"]["runs"] == 1
    assert benchmark["result"]["peakMemoryBytes"] > 0
    assert json.loads(output.read_text(encoding="utf-8"))["result"]["observed"] is True


def test_partial_strict_usage_and_input_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "large.py").write_bytes(b"x" * 2_000_001)

    assert main(["scan", str(root), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["diagnostics"][0]["code"] == "FILE_TOO_LARGE"
    assert main(["scan", str(root), "--strict", "--json"]) == 4
    capsys.readouterr()

    with pytest.raises(SystemExit) as invalid_type:
        main(["find-clones", str(root), "--type", "5"])
    assert invalid_type.value.code == 2
    with pytest.raises(SystemExit) as missing:
        main(["scan", str(tmp_path / "missing")])
    assert missing.value.code == 3


def test_help_and_invalid_benchmark_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
    assert "find-clones" in capsys.readouterr().out

    with pytest.raises(SystemExit) as invalid_runs:
        main(["benchmark", str(tmp_path), "--runs", "0"])
    assert invalid_runs.value.code == 2


def test_find_clones_supports_structural_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "structural"
    root.mkdir()
    (root / "base.py").write_text(
        Path("tests/benchmarks/corpus/m12-structural-v1/base.py").read_text()
    )
    (root / "near.py").write_text(
        Path("tests/benchmarks/corpus/m12-structural-v1/insert_delete.py").read_text()
    )

    assert main(["find-clones", str(root), "--type", "3", "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["result"]["matches"][0]["category"] == "type3"


def test_find_clones_supports_verified_semantic_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "semantic"
    root.mkdir()
    corpus = Path("tests/benchmarks/corpus/m14-verified-v1")
    (root / "sum.py").write_text((corpus / "sum.py").read_text())
    (root / "sum.js").write_text((corpus / "sum.js").read_text())

    assert (
        main(
            [
                "find-clones",
                str(root),
                "--type",
                "4",
                "--verify-semantic",
                "--format",
                "json",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    match = report["result"]["matches"][0]
    assert match["category"] == "type4"
    assert match["evidence_state"] == "verified"
    assert match["algorithm_version"].startswith("semantic-v2:")
