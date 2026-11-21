# Implementation Roadmap

Each milestone requires its referenced specifications, tests, review, and updated traceability; “files” below are planned module boundaries, not current implementation.

| M | Dependencies | Scope / planned modules | Required specs and tests | Definition of Done |
|---:|---|---|---|---|
| M0 | — | workspace, CI, config, versioning | requirements, architecture; doc/CI checks | reproducible build skeleton; no engine behavior |
| M1 | M0 | `core/adapters`, ingestion | language-adapters; TC-ING/LNG | four adapters pass spans and safety limits |
| M2 | M1 | `core/normalization` | algorithm-contracts; TC-NRM | both norm-v1 modes pass goldens |
| M3 | M2 | `core/fingerprint` | algorithm-contracts; TC-FPR/NFR-001 | rolling/Winnowing vectors deterministic |
| M4 | M3 | `index`, storage adapter | data-model; TC-IDX | atomic index replace and lookup pass |
| M5 | M4 | `core/retrieval` | algorithm-contracts; TC-RET | recall measured; limits explicit |
| M6 | M5 | `core/verification`, aggregation | algorithm-contracts; TC-VRF/CLS/SCR | ranges/types/scores/dedup pass |
| M7 | M6 | `cmd/opencode` | cli-contracts; TC-CLI | five commands and versioned outputs pass |
| M8 | M4/M6 | `api`, `persistence`, workers | api-contracts, data-model; TC-API/DB | async scans, migrations, auth/idempotency pass |
| M9 | M8 | `web` | API and acceptance; TC-WEB | accessible evidence/filter workflows pass |
| M10 | M6–M9 | `benchmark`, corpora manifests | test-cases; TC-BEN/NFR | reproducible observed report produced |
| M11 | M8–M10 | sandbox, quotas, telemetry, deployment | security/NFR; TC-SEC/OBS | threat controls and production gates pass |
| M12 | M6 | `core/structural` AST extension | REQ-EXT-001; TC-EXT | versioned experimental results remain distinct |

Acceptance for M0–M11 is [MVP criteria](../specs/acceptance-criteria.md). M12 is future and cannot delay the lexical MVP. A milestone does not close with disabled tests, undocumented contract drift, or unresolved high-severity defects.

## Milestone status

| Milestone | Status | Evidence |
|---:|---|---|
| M0 | complete | Python 3.12 verification: Ruff and mypy clean; 7 pytest tests passed with 100% core coverage; sdist/wheel built; documentation validation passed |
| M1 | complete | Python 3.12 verification: four pinned tree-sitter adapters and bounded scanner; 19 tests passed; 92.51% core coverage; Ruff/mypy/build/docs checks passed |
| M2 | complete | Python 3.12 verification: norm-v1 exact/renamed streams; 26 tests passed; 90.96% core coverage; Ruff/mypy/build/docs checks passed |
| M3–M12 | not started | Must proceed in dependency order |
