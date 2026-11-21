"""Reproducible corpus evaluation and performance measurement."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

from opencode_core.engine import analyze_directory, find_clones
from opencode_core.version import FINGERPRINT_VERSION, NORMALIZATION_VERSION, PACKAGE_VERSION


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))  # type: ignore[return-value]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _confusion(
    expected: set[tuple[str, str]],
    predicted: set[tuple[str, str]],
    universe: set[tuple[str, str]],
) -> dict[str, float | int]:
    predicted = predicted & universe
    tp = len(expected & predicted)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    tn = len(universe - expected - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "truePositives": tp,
        "falsePositives": fp,
        "falseNegatives": fn,
        "trueNegatives": tn,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "falsePositiveRate": fp / (fp + tn) if fp + tn else 0.0,
    }


def run_benchmark(
    corpus: Path,
    manifest_path: Path,
    *,
    repetitions: int = 5,
    warmups: int = 1,
    seed: int = 20261122,
    categories: tuple[str, ...] = ("type1", "type2"),
) -> dict[str, Any]:
    if repetitions < 1 or warmups < 0:
        raise ValueError("repetitions must be positive and warmups non-negative")
    corpus = corpus.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = sorted(corpus / item["path"] for item in manifest["files"])
    for path, item in zip(
        files, sorted(manifest["files"], key=lambda value: value["path"]), strict=True
    ):
        if _sha256(path) != item["sha256"]:
            raise ValueError(f"corpus checksum mismatch: {path.name}")
    for _ in range(warmups):
        find_clones(analyze_directory(corpus), categories)
    samples: list[dict[str, float | int]] = []
    predicted: dict[str, set[tuple[str, str]]] = {kind: set() for kind in categories}
    tracemalloc.start()
    for _ in range(repetitions):
        started = time.perf_counter()
        workspace = analyze_directory(corpus)
        scan_seconds = time.perf_counter() - started
        started = time.perf_counter()
        matches = find_clones(workspace, categories)
        search_seconds = time.perf_counter() - started
        for match in matches:
            predicted[match.category].add(_pair(match.left.fragment_id, match.right.fragment_id))
        lines = sum(path.read_bytes().count(b"\n") for path in files)
        samples.append(
            {
                "scanSeconds": scan_seconds,
                "searchSeconds": search_seconds,
                "files": len(files),
                "lines": lines,
                "matches": len(matches),
            }
        )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metric_categories = tuple(kind for kind in ("type1", "type2", "type3") if kind in categories)
    labels = {
        kind: {_pair(*pair) for pair in manifest["labels"].get(kind, [])}
        for kind in metric_categories
    }
    universe = {_pair(*pair) for pair in manifest["evaluatedPairs"]}
    scan_times = [float(item["scanSeconds"]) for item in samples]
    search_times = [float(item["searchSeconds"]) for item in samples]
    kloc = float(samples[0]["lines"]) / 1000
    serialized_index_bytes = len(
        json.dumps(
            [
                [record.fragment_id, item.hash_u64, item.token_position]
                for record in workspace.records
                for fingerprint_set in (record.exact_fingerprints, record.renamed_fingerprints)
                for item in fingerprint_set.fingerprints
            ],
            separators=(",", ":"),
        ).encode()
    )
    metrics: dict[str, Any] = {
        kind: {
            **_confusion(labels[kind], predicted[kind], universe),
            "candidateRecall": _confusion(labels[kind], predicted[kind], universe)["recall"],
        }
        for kind in metric_categories
    }
    if "type3" not in categories:
        metrics["type3"] = {"status": "not-implemented", "observed": False}
    metrics["type4Candidate"] = {"status": "not-implemented", "observed": False}
    metrics["type4Verified"] = {"status": "not-implemented", "observed": False}
    throughput = statistics.median(kloc / value for value in scan_times)
    return {
        "schemaVersion": "benchmark-v1",
        "observed": True,
        "manifest": {
            "id": manifest["id"],
            "sha256": _sha256(manifest_path),
            "files": [{"path": path.name, "sha256": _sha256(path)} for path in files],
        },
        "versions": {
            "package": PACKAGE_VERSION,
            "fingerprint": FINGERPRINT_VERSION,
            "normalization": NORMALIZATION_VERSION,
        },
        "environment": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "os": platform.platform(),
            "machine": platform.machine(),
        },
        "protocol": {"seed": seed, "warmups": warmups, "repetitions": repetitions},
        "samples": samples,
        "metricsByCategory": metrics,
        "performance": {
            "scanThroughputKlocPerSecondMedian": throughput,
            "searchLatencySecondsP50": statistics.median(search_times),
            "searchLatencySecondsP95": _percentile(search_times, 0.95),
            "searchLatencySecondsP99": _percentile(search_times, 0.99),
            "peakMemoryBytes": peak,
            "serializedIndexBytes": serialized_index_bytes,
            "serializedIndexBytesPerKloc": serialized_index_bytes / kloc,
        },
        "targets": {
            "scanThroughputKlocPerSecondMinimum": 20.0,
            "searchLatencySecondsP95MaximumAt10MPostings": 2.0,
            "peakMemoryBytesMaximumAt100Kloc": 262144000,
            "applicability": (
                "Targets require the specified scale; this small corpus is observed but not a "
                "target pass/fail run."
            ),
        },
    }


def write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
