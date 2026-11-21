# Requirements-to-Code Map

This map assigns approved requirement families to planned implementation boundaries. A path denotes ownership, not completion; milestone status is authoritative in the roadmap and release notes.

| Requirements | Owning paths | Milestone | Current status |
|---|---|---:|---|
| REQ-ING-* | `packages/core/src/opencode_core/parsers/`, future application ingestion service | M1/M8 | planned |
| REQ-LNG-* | `packages/core/src/opencode_core/parsers/` | M1 | planned |
| REQ-NRM-* | `packages/core/src/opencode_core/normalization/` | M2 | planned |
| REQ-FPR-*, REQ-NFR-001 | `packages/core/src/opencode_core/fingerprinting/` | M3 | planned |
| REQ-IDX-* | `packages/core/src/opencode_core/indexing/`, future PostgreSQL adapter | M4/M8 | planned |
| REQ-RET-* | `packages/core/src/opencode_core/retrieval/` | M5 | planned |
| REQ-VRF-*, REQ-CLS-*, REQ-SCR-* | `packages/core/src/opencode_core/matching/`, `classification/` | M6 | planned |
| REQ-CLI-* | `packages/cli/` | M7 | planned |
| REQ-API-* | `apps/api/`, `apps/worker/` | M8 | planned |
| REQ-WEB-* | `apps/web/` | M9 | planned |
| REQ-BEN-*, REQ-NFR-002 | `tests/benchmarks/` | M10 | planned |
| REQ-SEC-*, REQ-OBS-* | all boundaries; `infrastructure/` | M11 | planned |
| REQ-EXT-* | core ports and architecture tests | M12 | planned |

M0 owns `pyproject.toml`, configuration/version primitives, CI, validation scripts, and package/test boundaries. It implements no functional `REQ-*`; its acceptance is the reproducible build skeleton required by [the roadmap](../docs/18-implementation-roadmap.md).
