# Testing Strategy

The test pyramid emphasizes pure property/golden tests for normalization, hashing, tie behavior, spans, and scoring; adapter conformance tests; PostgreSQL transaction/integration tests; CLI/API contracts; then a small end-to-end and accessibility suite.

| Layer | Main technique | Required evidence |
|---|---|---|
| core | examples, property tests, mutation tests | deterministic vectors and invariants |
| parsers | licensed/synthetic goldens, fuzzing | tokens, Unicode coordinates, degraded parses |
| storage | real PostgreSQL, fault injection | atomic replacement, cascades, concurrency |
| retrieval | labeled corpus | candidate recall before verification |
| verification | adversarial pairs/collisions | exact spans, rejection, stable groups |
| interfaces | OpenAPI/JSON/SARIF snapshots | compatibility and error semantics |
| security | hostile trees, fuzzers, canary secrets | bounded use and no leakage |
| system | containerized workflows | user journeys and accessibility |
| structural | synthetic AST edits, dependency-aware reorder fixtures, held-out projects | per-edit-class precision/recall and explanations |
| semantic | pinned model corpus, syntactically diverse positives, adversarial hard negatives | candidate recall distinct from verified precision/recall |
| behavioral sandbox | escape, timeout, nondeterminism, I/O, generated input coverage | safe failure and tested-domain limitations |

Fixtures record source/license/checksum; random tests record seed; flaky retries do not count as passes. Datasets are split by repository into development and held-out evaluation sets to reduce leakage, and each clone category is reported separately. CI runs unit/contract tests on every change, integration/security subsets on pull requests, and full corpus/benchmarks on scheduled/release builds. Normative cases are in [test-cases.md](../specs/test-cases.md), with gates in [acceptance criteria](../specs/acceptance-criteria.md).
