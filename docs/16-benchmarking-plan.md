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
