"""Run the versioned M10 evaluation protocol."""

from __future__ import annotations

import argparse
from pathlib import Path

from opencode_core.benchmarking import run_benchmark, write_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus", type=Path, default=Path("tests/benchmarks/corpus/m10-synthetic-v1")
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tests/benchmarks/corpus/m10-synthetic-v1/manifest.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261122)
    args = parser.parse_args()
    write_report(
        run_benchmark(
            args.corpus,
            args.manifest,
            repetitions=args.repetitions,
            warmups=args.warmups,
            seed=args.seed,
        ),
        args.output,
    )


if __name__ == "__main__":
    main()
