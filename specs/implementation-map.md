# Requirements-to-Code Map

This map assigns approved requirement families to planned implementation boundaries. A path denotes ownership, not completion; milestone status is authoritative in the roadmap and release notes.

| Requirements | Owning paths | Milestone | Current status |
|---|---|---:|---|
| REQ-ING-* | `packages/core/src/opencode_core/parsers/`, future application ingestion service | M1/M8 | local safe scanning implemented; repository identity deferred to M8 |
| REQ-LNG-* | `packages/core/src/opencode_core/parsers/` | M1 | four pinned tree-sitter adapters implemented |
| REQ-NRM-* | `packages/core/src/opencode_core/normalization/` | M2 | norm-v1 exact and renamed streams implemented |
| REQ-FPR-*, REQ-NFR-001 | `packages/core/src/opencode_core/fingerprinting/` | M3 | fp-v1 rolling hash, Winnowing, SMALL, and compatibility checks implemented |
| REQ-IDX-* | `packages/core/src/opencode_core/indexing/`, `apps/api` relational schema | M4/M8 | atomic in-memory index plus PostgreSQL-compatible fingerprint/posting persistence implemented |
| REQ-RET-* | `packages/core/src/opencode_core/retrieval/` | M5 | bounded retrieval, stop-fingerprint policy, and positional evidence implemented |
| REQ-VRF-*, REQ-CLS-*, REQ-SCR-* | `packages/core/src/opencode_core/matching/`, `detection/` | M6 | Type 1/2 verification, source mapping, classification, scores, and common results implemented |
| REQ-CLI-* | `packages/cli/`, `opencode_core.engine` | M7 | five standalone commands, JSON/SARIF, help, errors, and exit codes implemented |
| REQ-API-* | `apps/api/`, `apps/worker/` | M8 | FastAPI resources, durable scan jobs, SQLAlchemy schema, Alembic migration, and worker implemented |
| REQ-WEB-* | `apps/web/` | M9 | planned |
| REQ-BEN-*, REQ-NFR-002 | `tests/benchmarks/` | M10 | planned |
| REQ-SEC-*, REQ-OBS-* | all boundaries; `infrastructure/` | M11 | planned |
| REQ-ENG-*, REQ-RPT-* | `packages/core/src/opencode_core/detection/`, result aggregation | M6/M12 | common interface/result schema and lexical detectors implemented; structural/semantic aggregation pending |
| REQ-T3-* | `packages/core/src/opencode_core/structural/` | M12 | planned structural engine |
| REQ-T4-* | `packages/core/src/opencode_core/semantic/` | M13/M14 | planned experimental retrieval then multi-evidence verification |
| REQ-EVL-* | `tests/benchmarks/`, versioned evaluation manifests | M10/M12/M13/M14 | planned per-category evaluation |

M0 owns `pyproject.toml`, configuration/version primitives, CI, validation scripts, and package/test boundaries. It implements no functional `REQ-*`; its acceptance is the reproducible build skeleton required by [the roadmap](../docs/18-implementation-roadmap.md).
