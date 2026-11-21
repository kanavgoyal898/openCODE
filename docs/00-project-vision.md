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

Type 3 and semantic Type 4 detection, calibrated confidence, and AST/PDG/embedding engines are future work. Success is governed by [formal requirements](../specs/requirements.md) and [acceptance criteria](../specs/acceptance-criteria.md).
