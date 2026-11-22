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
| REQ-WEB-* | `apps/web/` | M9 | API-backed scan state, filters, evidence metadata, source ranges, direct snippet comparison, responsive layouts, caveat, and accessible keyboard flow implemented |
| REQ-BEN-*, REQ-NFR-002 | `opencode_core.benchmarking`, `scripts/run_benchmarks.py`, `tests/benchmarks/` | M10 | reproducible manifest validation, category metrics, raw samples, environment, observed/target separation implemented; scale targets remain explicitly unevaluated on small corpus |
| REQ-SEC-*, REQ-OBS-* | ingestion settings/scanner, API middleware/admission, service containers and Compose | M11 | total-byte/request/active-scan bounds, default source suppression, safe request telemetry and headers, non-root read-only restricted containers, and internal backend network implemented |
| REQ-ENG-*, REQ-RPT-* | detection model, lexical/structural/semantic engines, engine aggregation | M6/M12/M13/M14 | common result schema, four pluggable detectors, stable cross-engine deduplication, evidence states, versions, source ranges, explanations, and limitations implemented |
| REQ-T3-* | `opencode_core.structural`, AST node adapter output, CLI/API/worker integration | M12 | `struct-v1` MinHash/LSH retrieval, AST/token verification, conservative reorder evidence, and observed labeled evaluation implemented |
| REQ-T4-* | `opencode_core.semantic`, model/evidence cards, CLI/API/worker integration | M13/M14 | pinned embedding candidate retrieval plus opt-in CFG, def-use, and PDG-style promotion implemented; unsupported constructs remain candidates; bounded behavioral harness is separately authorized |
| REQ-EVL-* | `tests/benchmarks/`, versioned evaluation manifests | M10/M12/M13/M14 | separate observed Type 1/2, Type 3, Type 4 candidate, and Type 4 verified reports implemented; production-scale and broad semantic evaluation remain outstanding targets |

M0 owns `pyproject.toml`, configuration/version primitives, CI, validation scripts, and package/test boundaries. It implements no functional `REQ-*`; its acceptance is the reproducible build skeleton required by [the roadmap](../docs/18-implementation-roadmap.md).
