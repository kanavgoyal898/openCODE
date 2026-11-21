# Risk Register

| ID | Risk | Likelihood / impact | Mitigation | Trigger / owner |
|---|---|---|---|---|
| RSK-001 | parser defects or grammar drift change tokens | M/H | pin checksums, goldens, fuzz, version adapters | golden diff / compiler lead |
| RSK-002 | frequent boilerplate floods candidates | H/H | stop-fingerprints, quotas, DF metrics, strict verification | candidate ratio alert / IR lead |
| RSK-003 | 64-bit collision creates false seed | L/M | canonical token verification, collision fixture | unequal verified tokens / engine lead |
| RSK-004 | normalization hides meaningful differences | M/H | conservative roles, separate modes/scores, corpus review | precision regression / research lead |
| RSK-005 | stale postings after update/delete | M/H | transactional replace, cascades, outbox deletion, audits | orphan audit / storage lead |
| RSK-006 | hostile repository exhausts service | H/H | isolation and layered budgets | quota kills/queue age / security lead |
| RSK-007 | private source or credentials leak | M/Critical | least retention, encryption, redaction, canary tests | canary detection / security lead |
| RSK-008 | users interpret similarity as plagiarism | H/H | UI/API caveat and evidence vocabulary | support/legal report / product lead |
| RSK-009 | target performance misses at 10M postings | M/H | benchmark early, profile, partition only with evidence | M10 gate / performance lead |
| RSK-010 | multi-language coordinate inconsistency | M/H | byte + line/column contract, Unicode/CRLF goldens | span mismatch / compiler lead |
| RSK-011 | uncertain PostgreSQL unsigned representation | M/M | resolve before M4 migration; benchmark numeric vs signed mapping | M4 planning / storage lead |
| RSK-012 | clone-group stability across policy versions | M/M | include all versions/policy in signature | result drift / engine lead |

Risks are reviewed at each milestone; accepted residual risk needs owner, expiry, and decision record. RSK-011 is the sole unresolved implementation choice and is bounded by [ADR-005](adr/ADR-005-storage-strategy.md).
