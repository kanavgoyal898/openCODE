# Benchmarking and Evaluation Plan

Use two corpora: deterministic synthetic transformations with known clone spans and a frozen manifest of permissively licensed projects with manually reviewed pairs. Split calibration/development from held-out evaluation even though MVP confidence is uncalibrated. Record repository commits, licenses, checksums, grammar/config versions, seed, hardware, OS, runtime, warmup, repetitions, and raw samples.

| Metric | Definition |
|---|---|
| precision / recall / F1 | TP/(TP+FP), TP/(TP+FN), harmonic mean at span-overlap labeling rule |
| candidate recall | labeled clones with ≥1 retrieved candidate / all labeled clones |
| false-positive rate | non-clone pairs incorrectly verified / evaluated non-clone pairs |
| throughput | parsed source KLOC / wall-clock scan seconds |
| latency | p50/p95/p99 end-to-end search over fixed query set |
| storage | fingerprint/posting bytes per indexed KLOC |
| memory | peak resident set per workload |

Run at least five measured repetitions after one warmup; report median and dispersion, not only the best run. Include cold/warm cache, 1/10/100 KLOC, and 1M/10M postings. Targets from [non-functional requirements](03-non-functional-requirements.md) appear in a separate column from observed values. Failed/truncated runs remain in the report with cause.

Type 1, Type 2, Type 3, Type 4 candidate retrieval, and Type 4 verified results receive separate confusion matrices and retrieval metrics. Type 3 reports each transformation class. Type 4 reports model/index versions, cosine distributions, ANN recall against exact neighbors, hard-negative false positives, and the incremental effect of CFG/data-flow/PDG/behavioral evidence. No benchmark result may be invented or generalized beyond its dataset.

## M10 observed baseline

The checked-in [raw report](../tests/benchmarks/results/m10-observed-macos-arm64.json) was measured on the checksummed 36-line `m10-synthetic-v1` corpus using one warmup and five repetitions. Type 1 and Type 2 each observed precision, recall, and F1 of 1.0 for one positive and three evaluated negatives. Median scan throughput was 2.80 KLOC/s, p95 search latency was 2.58 ms, peak traced Python memory was 210,346 bytes, and the deterministic serialized-index estimate was 3,244 bytes. These are small-corpus observations, not evidence that the 20 KLOC/s, 10M-posting, or 100-KLOC targets pass. Type 3 and both Type 4 states are explicitly `not-implemented` in this M10 report and will receive new versioned reports at M12–M14.
