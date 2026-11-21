# Requirements Traceability Matrix

The complete one-row-per-requirement mapping is maintained in [requirements.md](requirements.md); this view maps requirement families to contracts, acceptance gates, and implementation milestones without duplicating requirement definitions.

| Requirement family | Normative contract | Test cases | Acceptance | Milestone |
|---|---|---|---|---:|
| REQ-ING-* | [architecture](architecture.md), [language adapters](language-adapters.md) | TC-ING-* | AC-001 | M1/M8 |
| REQ-LNG-* | [language adapters](language-adapters.md) | TC-LNG-* | AC-001 | M1 |
| REQ-NRM-* | [algorithm contracts](algorithm-contracts.md) | TC-NRM-* | AC-001/002 | M2 |
| REQ-FPR-* | [algorithm contracts](algorithm-contracts.md) | TC-FPR-* | AC-004 | M3 |
| REQ-IDX-* | [data model](data-model.md) | TC-IDX-*, TC-DB-001 | AC-005 | M4/M8 |
| REQ-RET-* | [algorithm contracts](algorithm-contracts.md) | TC-RET-* | AC-003 | M5 |
| REQ-VRF-*, REQ-CLS-*, REQ-SCR-* | [algorithm contracts](algorithm-contracts.md) | TC-VRF-*, TC-CLS-*, TC-SCR-* | AC-002/009 | M6 |
| REQ-CLI-* | [CLI contracts](cli-contracts.md) | TC-CLI-* | AC-006 | M7 |
| REQ-API-* | [API contracts](api-contracts.md) | TC-API-* | AC-006 | M8 |
| REQ-WEB-* | [architecture](architecture.md) | TC-WEB-* | AC-009 | M9 |
| REQ-BEN-*, REQ-NFR-* | [test cases](test-cases.md) | TC-BEN-*, TC-NFR-* | AC-002/003/008 | M10 |
| REQ-SEC-*, REQ-OBS-* | [data model](data-model.md), [API](api-contracts.md) | TC-SEC-*, TC-OBS-* | AC-007 | M11 |
| REQ-EXT-* | [architecture](architecture.md) | TC-EXT-* | future gate | M12 |

Changes to a requirement must update its row, referenced contract, tests, and acceptance gate in the same change. Orphan tests may exist only when labeled regression or exploratory.
