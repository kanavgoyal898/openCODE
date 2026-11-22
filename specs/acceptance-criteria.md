# Acceptance Criteria

## MVP release gate (M0–M11)

The Phase 1 lexical MVP is acceptable when its Type 1/2 requirements pass. Complete-project acceptance additionally requires the Phase 2–4 gates below. No critical/high security finding may remain, migrations must restore from backup, and every evaluation must publish a reproducibility manifest.

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
| AC-009 | Web evidence is responsive and accessible, source ranges are exact, direct snippet comparison works, and every result carries the non-plagiarism caveat. | TC-WEB-001..004, TC-VRF-001..005 |
| AC-010 | All requirement rows have milestone and test mappings, and all normative links validate. | documentation validation script/checklist |
| AC-011 | Type 3 handles the five required edit classes with held-out precision and recall targets approved before evaluation; approximate retrieval recall is reported separately. | TC-T3-001..006, TC-EVL-003 |
| AC-012 | Type 4 embedding retrieval is explicitly experimental/candidate-only and publishes model card, dataset, ANN recall, hard-negative behavior, and per-model version. | TC-T4-001..005 |
| AC-013 | Any verified Type 4 result has at least two approved non-embedding evidence sources; optional behavioral checks pass sandbox escape/resource tests and retain tested-domain limitations. | TC-T4-006..010 |
| AC-014 | Unified reports deduplicate cross-engine results without erasing evidence, return source locations/explanations, and expose separate metrics per category and evidence state. | TC-RPT-001..004, TC-EVL-001..004 |

Type 3 and Type 4 are complete-project requirements delivered after the lexical MVP. Type 4 embedding similarity alone is never accepted as verified equivalence. Remote multi-tenant production hosting remains separately gated.
