from __future__ import annotations

import json
from pathlib import Path

import pytest
from opencode_core.benchmarking import run_benchmark, write_report

CORPUS = Path("tests/benchmarks/corpus/m10-synthetic-v1")


def test_reproducible_manifest_metrics_and_observed_targets(tmp_path: Path) -> None:
    report = run_benchmark(CORPUS, CORPUS / "manifest.json", repetitions=2, warmups=1)
    assert report["observed"] is True
    assert report["protocol"] == {"seed": 20261122, "warmups": 1, "repetitions": 2}
    assert report["metricsByCategory"]["type1"]["recall"] == 1
    assert report["metricsByCategory"]["type2"]["recall"] == 1
    assert report["metricsByCategory"]["type4Candidate"]["observed"] is False
    assert "Minimum" in "".join(report["targets"])
    output = tmp_path / "report.json"
    write_report(report, output)
    assert json.loads(output.read_text())["manifest"]["id"] == "m10-synthetic-v1"


def test_checksum_and_protocol_validation(tmp_path: Path) -> None:
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    manifest["files"][0]["sha256"] = "0" * 64
    changed = tmp_path / "manifest.json"
    changed.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="checksum mismatch"):
        run_benchmark(CORPUS, changed)
    with pytest.raises(ValueError, match="repetitions"):
        run_benchmark(CORPUS, CORPUS / "manifest.json", repetitions=0)


def test_structural_evaluation_reports_separate_metrics() -> None:
    corpus = Path("tests/benchmarks/corpus/m12-structural-v1")
    report = run_benchmark(
        corpus,
        corpus / "manifest.json",
        repetitions=1,
        warmups=0,
        categories=("type3",),
    )
    assert report["metricsByCategory"]["type3"]["precision"] == 1
    assert report["metricsByCategory"]["type3"]["recall"] == 1


def test_semantic_evaluation_is_candidate_only() -> None:
    corpus = Path("tests/benchmarks/corpus/m13-semantic-v1")
    report = run_benchmark(
        corpus,
        corpus / "manifest.json",
        repetitions=1,
        warmups=0,
        categories=("type4",),
    )
    assert report["metricsByCategory"]["type4Candidate"]["recall"] == 1
    assert report["metricsByCategory"]["type4Verified"]["observed"] is False
