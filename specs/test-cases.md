# Normative Test Cases

All fixtures are synthetic or carry a recorded permissive license and checksum. Golden output includes pinned tool/grammar/config versions.

## Ingestion and security

| ID | Scenario | Expected result |
|---|---|---|
| TC-ING-001 | Tree with includes, excludes, binary, and symlink escape | allowed text only; skips diagnosed; escape rejected |
| TC-ING-002 | Ingest same revision twice | one logical revision; idempotent scan |
| TC-SEC-001 | Source contains import, static initializer, build hook | none executes |
| TC-SEC-002..007 | traversal, symlink loop, huge file, depth bomb, token bomb, malformed parse | bounded rejection with stable error |
| TC-SEC-008..010 | credential URL, raw source, retention expiry | secrets/source absent from logs; data deleted on schedule |

## Language and normalization

| ID | Scenario | Expected result |
|---|---|---|
| TC-LNG-001..004 | Representative fixture for each supported language | ordered tokens and exact source spans match golden |
| TC-LNG-005 | CRLF, astral Unicode identifier, combining characters | byte/line/column mapping matches contract |
| TC-NRM-001 | Run same input 100 times/processes | identical stream |
| TC-NRM-002 | Formatting/comments differ | exact and renamed streams equal |
| TC-NRM-003 | Consistent identifier rename | exact differs; renamed equals |
| TC-NRM-004 | String/number variants | behavior matches literal matrix |
| TC-NRM-005 | Shadowed/local/member identifiers | role-aware placeholders are deterministic |
| TC-NRM-006 | parse coverage below threshold | skip diagnostic; no fingerprints |

## Fingerprinting, retrieval, verification

| ID | Scenario | Expected result |
|---|---|---|
| TC-FPR-001..004 | fixed vector, tie, short stream, rolling-vs-naive property | exact golden hashes/positions |
| TC-FPR-005 | mixed algorithm versions | rejected before retrieval |
| TC-IDX-001 | index/query known postings | all and only expected postings with positions |
| TC-IDX-002 | update file while injected transaction failure occurs | old complete revision or new complete revision, never mixed |
| TC-RET-001..003 | common span, stop hash, stable ties | candidate recall/order meet contract |
| TC-VRF-001..005 | seed expansion, gaps, overlap, collision, no-match | exact spans, deduplication, collision rejection, empty result |
| TC-CLS-001..003 | exact, renamed, merely similar | Type 1, Type 2, or unclassified respectively |
| TC-SCR-001 | known streams | each score independently recomputes; confidence is null |

## CLI and API

| ID | Scenario | Expected result |
|---|---|---|
| TC-CLI-001..006 | each command, JSON, partial, interruption | schema and exit codes match contract |
| TC-API-001..010 | endpoint success/error/idempotency/pagination/auth | OpenAPI-valid responses and tenant isolation |
| TC-API-011 | compare two submitted snippets in exact and renamed modes | deterministic verified evidence; input is not persisted; no-match returns an empty successful result |
| TC-DB-001 | delete repository | no queryable relational/blob-derived data remains |
| TC-WEB-001..003 | filters/evidence/keyboard and screen reader | correct results, WCAG 2.2 AA critical paths |
| TC-WEB-004 | compare two snippets at phone, tablet, and desktop widths | accessible inputs and status; stacked narrow layout and side-by-side wide layout; evidence and no-match states are clear |
| TC-BEN-001 | repeated pinned corpus/seed | report contains reproducibility manifest |
| TC-BEN-002 | target comparison | measured values labeled observed; targets labeled target |
| TC-NFR-001 | cross-platform golden run | byte-identical ordered JSON excluding declared timing fields |
| TC-NFR-002 | 10M-posting benchmark | report all latency/throughput/memory metrics, pass/fail targets |
| TC-OBS-001 | exercise all failures with canary secrets | no canary in logs/traces/metrics |
| TC-EXT-001 | in-memory ports with no DB/web imports | fingerprint engine operates independently |

## Structural and semantic engines

| ID | Scenario | Expected result |
|---|---|---|
| TC-ENG-001..004 | instantiate each detector through common interface with independent configs | common result schema; no concrete-engine coupling |
| TC-T3-001 | statement insertion/deletion | verified Type 3 with edit explanation and exact ranges |
| TC-T3-002 | modified expression | structural/token scores reflect modification |
| TC-T3-003 | independent statement reorder | reorder evidence accepted only after dependency check |
| TC-T3-004 | dependent statement reorder | not credited as independent; reject or lower score |
| TC-T3-005 | partial structural clone and unrelated negative | positive verified; negative rejected |
| TC-T3-006 | LSH held-out corpus | candidate recall and verification precision/recall reported |
| TC-T4-001..005 | pinned model determinism, ANN recall, syntactic diversity, hard negatives, truncation | candidate-only results with model evidence and limitations |
| TC-T4-006..009 | CFG/data-flow/PDG evidence, unsupported constructs, sandbox escape, timeout | promotion only under approved evidence policy; safe failure |
| TC-T4-010 | behavioral checks over generated inputs | tested-domain evidence recorded; no universal-equivalence claim |
| TC-RPT-001..004 | cross-engine duplicate, source ranges, versions/thresholds, explanations | one unified result retaining every engine's evidence/state |
| TC-EVL-001..004 | held-out Type 1–4 evaluation | separate precision/recall/F1/retrieval/performance metrics and manifests |
