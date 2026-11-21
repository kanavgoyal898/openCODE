# Project Vision

openCODE makes large-scale code similarity inspectable and reproducible. It serves maintainers, researchers, migration teams, and reviewers who need to locate duplicated lexical structure and see the exact evidence and source ranges behind each result.

The MVP scans local directories and repository revisions; supports Python, JavaScript, TypeScript, and Java; detects formatting-only and identifier-renamed clones; and exposes a standalone engine, CLI, REST API, workers, and accessible web results. Its core promise is deterministic evidence: pinned input and versions yield the same ordered fingerprints and matches.

## Principles and boundaries

- Retrieve broadly, verify strictly, and expose both stages separately.
- Never execute source under analysis; treat repositories as hostile input.
- Keep raw source retention minimal and configurable.
- Report fingerprint overlap and verified token similarity, never an uncalibrated probability.
- Say explicitly that similarity is not proof of plagiarism, intent, or ownership.
- Version adapters, normalization, fingerprints, schemas, and reports.

Delivery is phased: the lexical MVP provides Type 1/2; the complete project adds verified structural Type 3 detection, experimental Type 4 retrieval, and multi-evidence Type 4 verification. Embedding similarity is never semantic proof. Success is governed by [formal requirements](../specs/requirements.md), [detector contracts](../specs/detection-engines.md), and [acceptance criteria](../specs/acceptance-criteria.md).
