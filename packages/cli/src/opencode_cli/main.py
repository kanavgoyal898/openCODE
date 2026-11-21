"""Argument parsing and versioned reports for the standalone CLI."""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path
from typing import Any, NoReturn

from opencode_core.engine import analyze_directory, compare_files, find_clones
from opencode_core.version import (
    FINGERPRINT_VERSION,
    NORMALIZATION_VERSION,
    PACKAGE_VERSION,
    REPORT_SCHEMA_VERSION,
)

EXIT_PARTIAL = 1
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_ANALYSIS = 4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opencode", description="Evidence-based code clone detection"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {PACKAGE_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan and fingerprint a source directory")
    scan.add_argument("path", type=Path)
    _common_scan_options(scan)

    clones = subparsers.add_parser("find-clones", help="find verified clones in a directory")
    clones.add_argument("path", type=Path)
    clones.add_argument("--type", default="1,2", help="comma-separated clone types (1,2)")
    clones.add_argument("--min-tokens", type=int, default=28)
    clones.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    clones.add_argument("--exclude", action="append", default=[])
    clones.add_argument("--json", action="store_true")

    compare = subparsers.add_parser("compare", help="compare two source files")
    compare.add_argument("file1", type=Path)
    compare.add_argument("file2", type=Path)
    compare.add_argument("--mode", choices=("exact", "renamed"))
    compare.add_argument("--json", action="store_true")

    stats = subparsers.add_parser("stats", help="report repository fingerprint statistics")
    stats.add_argument("path", type=Path)
    _common_scan_options(stats)

    benchmark = subparsers.add_parser("benchmark", help="measure scan and retrieval on a corpus")
    benchmark.add_argument("corpus", nargs="?", type=Path, default=Path.cwd())
    benchmark.add_argument("--runs", type=int, default=1)
    benchmark.add_argument("--seed", type=int, default=20261122)
    benchmark.add_argument("--output", type=Path)
    benchmark.add_argument("--json", action="store_true")
    return parser


def _common_scan_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")


def _report(command: str, result: Any, diagnostics: list[Any], elapsed: float) -> dict[str, Any]:
    return {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "command": command,
        "algorithmVersion": FINGERPRINT_VERSION,
        "normalizationVersion": NORMALIZATION_VERSION,
        "result": result,
        "diagnostics": diagnostics,
        "timing": {"elapsedSeconds": elapsed},
    }


def _emit(report: dict[str, Any], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return
    result = report["result"]
    if isinstance(result, dict):
        for key, value in result.items():
            if key != "matches":
                print(f"{key}: {value}")
        for match in result.get("matches", []):
            print(
                f"{match['category']} {match['evidence_state']}: "
                f"{match['left']['fragment_id']}:{match['left']['start_line']}-"
                f"{match['left']['end_line']} <-> {match['right']['fragment_id']}:"
                f"{match['right']['start_line']}-{match['right']['end_line']}"
            )
    else:
        print(result)
    for diagnostic in report["diagnostics"]:
        print(f"{diagnostic['code']}: {diagnostic['message']}", file=sys.stderr)


def _fail(message: str, code: int) -> NoReturn:
    print(f"opencode: {message}", file=sys.stderr)
    raise SystemExit(code)


def _serialized_matches(matches: tuple[Any, ...]) -> list[dict[str, Any]]:
    return [asdict(match) for match in matches]


def _diagnostics(items: tuple[Any, ...]) -> list[dict[str, Any]]:
    return [{"path": str(item.path), "code": item.code, "message": item.message} for item in items]


def _sarif(matches: tuple[Any, ...]) -> dict[str, Any]:
    results = []
    for match in matches:
        results.append(
            {
                "ruleId": f"opencode-{match.category}",
                "level": "note",
                "message": {
                    "text": f"{match.category} {match.evidence_state}: "
                    "similarity is evidence, not proof of plagiarism"
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": match.left.fragment_id},
                            "region": {
                                "startLine": match.left.start_line,
                                "endLine": match.left.end_line,
                            },
                        }
                    }
                ],
                "relatedLocations": [
                    {
                        "id": 1,
                        "physicalLocation": {
                            "artifactLocation": {"uri": match.right.fragment_id},
                            "region": {
                                "startLine": match.right.start_line,
                                "endLine": match.right.end_line,
                            },
                        },
                    }
                ],
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "openCODE"}}, "results": results}],
    }


def _scan_result(path: Path, excludes: tuple[str, ...]) -> tuple[Any, dict[str, Any], float]:
    started = time.perf_counter()
    workspace = analyze_directory(path, excludes)
    elapsed = time.perf_counter() - started
    result = {
        "repositoryId": workspace.repository_id,
        "root": str(workspace.root),
        "files": len(workspace.records),
        "tokens": sum(len(record.exact_tokens) for record in workspace.records),
        "fingerprints": sum(
            len(record.exact_fingerprints.fingerprints)
            + len(record.renamed_fingerprints.fingerprints)
            for record in workspace.records
        ),
        "skips": len(workspace.diagnostics),
    }
    return workspace, result, elapsed


def _run(args: argparse.Namespace) -> int:
    if args.command in {"scan", "stats"}:
        workspace, result, elapsed = _scan_result(args.path, tuple(args.exclude))
        diagnostics = _diagnostics(workspace.diagnostics)
        _emit(_report(args.command, result, diagnostics, elapsed), args.json)
        return EXIT_ANALYSIS if args.strict and diagnostics else EXIT_PARTIAL if diagnostics else 0
    if args.command == "find-clones":
        workspace, summary, scan_elapsed = _scan_result(args.path, tuple(args.exclude))
        selected = tuple(f"type{value.strip()}" for value in args.type.split(","))
        if not set(selected) <= {"type1", "type2", "type3"}:
            _fail("only implemented clone types 1, 2, and 3 may be selected", EXIT_USAGE)
        started = time.perf_counter()
        matches = find_clones(workspace, selected, args.min_tokens)
        elapsed = scan_elapsed + time.perf_counter() - started
        summary["matches"] = _serialized_matches(matches)
        summary["matchCount"] = len(matches)
        diagnostics = _diagnostics(workspace.diagnostics)
        if args.format == "sarif":
            print(json.dumps(_sarif(matches), sort_keys=True, separators=(",", ":")))
            return EXIT_PARTIAL if diagnostics else 0
        json_mode = args.json or args.format == "json"
        _emit(_report(args.command, summary, diagnostics, elapsed), json_mode)
        return EXIT_PARTIAL if diagnostics else 0
    if args.command == "compare":
        started = time.perf_counter()
        matches = compare_files(args.file1, args.file2)
        if args.mode == "exact":
            matches = tuple(item for item in matches if item.category == "type1")
        elif args.mode == "renamed":
            matches = tuple(item for item in matches if item.category == "type2")
        result = {"matchCount": len(matches), "matches": _serialized_matches(matches)}
        _emit(_report(args.command, result, [], time.perf_counter() - started), args.json)
        return 0
    if args.command == "benchmark":
        if args.runs <= 0:
            _fail("--runs must be positive", EXIT_USAGE)
        samples = []
        tracemalloc.start()
        for _ in range(args.runs):
            workspace, summary, elapsed = _scan_result(args.corpus, ())
            started = time.perf_counter()
            matches = find_clones(workspace)
            samples.append(
                {
                    "scanSeconds": elapsed,
                    "retrievalSeconds": time.perf_counter() - started,
                    "files": summary["files"],
                    "tokens": summary["tokens"],
                    "matches": len(matches),
                }
            )
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result = {
            "observed": True,
            "seed": args.seed,
            "runs": args.runs,
            "samples": samples,
            "peakMemoryBytes": peak,
        }
        report = _report(args.command, result, [], sum(item["scanSeconds"] for item in samples))
        encoded = json.dumps(report, sort_keys=True, indent=2)
        if args.output:
            args.output.write_text(encoded + "\n", encoding="utf-8")
        _emit(report, args.json)
        return 0
    _fail("unknown command", EXIT_USAGE)


def main(argv: list[str] | None = None) -> int:
    try:
        return _run(_parser().parse_args(argv))
    except (FileNotFoundError, NotADirectoryError, PermissionError) as error:
        _fail(str(error), EXIT_INPUT)
    except ValueError as error:
        _fail(str(error), EXIT_ANALYSIS)


if __name__ == "__main__":
    raise SystemExit(main())
