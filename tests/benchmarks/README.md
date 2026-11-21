# Benchmarks

Run the pinned M10 protocol with:

```sh
python -m scripts.run_benchmarks --output tests/benchmarks/results/m10-observed.json
```

The checked-in synthetic corpus has a license, seed, labels, evaluated negatives, and SHA-256 for every file. The report records environment and algorithm versions, one warmup, five measured repetitions, raw samples, separate Type 1/2 confusion metrics, explicit not-implemented states for later engines, latency percentiles, throughput, peak traced memory, and targets in a separate object. The small fixture does not claim the 10M-posting or 100-KLOC target gates.

M12 uses the same runner with `--corpus tests/benchmarks/corpus/m12-structural-v1 --manifest tests/benchmarks/corpus/m12-structural-v1/manifest.json --categories type3` and persists its observed structural report separately.
