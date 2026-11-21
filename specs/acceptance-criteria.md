# Acceptance Criteria

## MVP release gate (M0–M11)

The MVP is acceptable only when all mandatory requirements in [requirements.md](requirements.md) except future `REQ-EXT-001` pass their mapped tests, no critical/high security finding remains, migrations restore from backup, and the reproducibility manifest is published with the release artifact.

| AC ID | Criterion | Evidence |
|---|---|---|
| AC-001 | Four adapters pass lexical/span goldens and malformed-input limits. | TC-LNG-001..005, TC-SEC-002..007 |
| AC-002 | Type 1 and Type 2 corpus precision ≥0.95 and recall ≥0.90; results identify corpus/version and are observed, not claimed in advance. | benchmark report, TC-BEN-001 |
| AC-003 | Candidate retrieval recall ≥0.98 on the labeled MVP corpus before verification. | retrieval evaluation |
| AC-004 | Fingerprint vectors, tie behavior, short inputs, collision defense, and cross-platform determinism pass. | TC-FPR-001..005, TC-NFR-001 |
| AC-005 | Incremental update and repository deletion leave no stale queryable postings. | TC-IDX-002, TC-DB-001 |
| AC-006 | API and CLI conform exactly to their versioned schemas and no-match is successful. | TC-API-001..010, TC-CLI-001..006 |
| AC-007 | Security limits, tenant authorization, secret redaction, and source retention pass adversarial tests. | TC-SEC-001..010, threat review |
| AC-008 | Targets in `REQ-NFR-002` are measured on declared hardware; misses block production release but not an explicitly labeled preview. | TC-NFR-002 |
| AC-009 | Web evidence is accessible, source ranges are exact, and every result carries the non-plagiarism caveat. | TC-WEB-001..003, TC-VRF-001..005 |
| AC-010 | All requirement rows have milestone and test mappings, and all normative links validate. | documentation validation script/checklist |

Type 3, Type 4, calibrated confidence, AST/PDG/embedding retrieval, and remote multi-tenant production hosting are not MVP acceptance claims unless separately approved and versioned.
