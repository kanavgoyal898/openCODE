# Non-Functional Requirements

| Quality | Target / rule | Verification |
|---|---|---|
| Determinism | byte-identical ordered results for pinned inputs/versions, excluding declared runtime fields | TC-NFR-001 |
| Performance | ≥20 KLOC/s/worker; p95 search ≤2 s at 10M postings | TC-NFR-002 |
| Memory | ≤250 MiB peak per 100 KLOC benchmark fixture | TC-NFR-002 |
| Availability | API target 99.9% monthly after production launch; workers are retryable/idempotent | operations SLO review |
| Security | hostile input isolation, no execution, least privilege, secret/source redaction | TC-SEC-* |
| Accessibility | critical web flows WCAG 2.2 AA | TC-WEB-003 |
| Portability | Linux/macOS CLI; OCI deployment; deterministic little/big-endian serialization | conformance matrix |
| Maintainability | dependency inversion, ≥90% core branch coverage target, ADRs for breaking decisions | CI/architecture tests |

Performance numbers are targets until measured on declared hardware and corpus. Capacity is protected by bounded files, depth, tokens, postings, candidates, wall time, queues, and tenant quotas. See [benchmarking](16-benchmarking-plan.md) and [security](14-security-threat-model.md).
