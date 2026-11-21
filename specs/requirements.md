# Formal Requirements

This file is the normative requirements baseline for openCODE. “Must” denotes an MVP obligation; future items are explicitly marked.

| ID | Requirement | Milestone | Verification | Tests |
|---|---|---:|---|---|
| REQ-ING-001 | Scan a local directory without executing analyzed code, while honoring configured exclusions. | M1 | integration | TC-ING-001, TC-SEC-001 |
| REQ-ING-002 | Ingest an immutable repository revision and assign stable repository, file, and revision identities. | M8 | integration | TC-ING-002 |
| REQ-LNG-001 | Detect and tokenize Python, JavaScript, TypeScript, and Java through replaceable adapters. | M1 | conformance | TC-LNG-001..004 |
| REQ-LNG-002 | Emit token source spans using UTF-8 byte offsets plus one-based line and column coordinates. | M1 | property test | TC-LNG-005 |
| REQ-NRM-001 | Produce deterministic `exact` and `renamed` token streams under normalization version `norm-v1`. | M2 | golden/property | TC-NRM-001..006 |
| REQ-NRM-002 | Remove comments and layout, canonicalize identifiers for renamed mode, and apply the literal policy in the algorithm contract. | M2 | golden | TC-NRM-002..005 |
| REQ-FPR-001 | Generate unsigned 64-bit polynomial rolling hashes over 25-token k-grams and select fingerprints with rightmost-minimum Winnowing over four hashes. | M3 | golden/property | TC-FPR-001..004 |
| REQ-FPR-002 | Persist algorithm and normalization versions with every fingerprint set and never compare incompatible versions. | M3 | integration | TC-FPR-005 |
| REQ-IDX-001 | Maintain an inverted index from `(algorithm_version, mode, hash)` to revision/fragment/token positions. | M4 | integration | TC-IDX-001 |
| REQ-IDX-002 | Atomically replace all derived records for an updated file revision; repository deletion must cascade to derived data. | M4/M8 | transaction test | TC-IDX-002, TC-DB-001 |
| REQ-RET-001 | Retrieve candidates by shared fingerprints, suppress configured high-frequency hashes, and retain position evidence. | M5 | integration | TC-RET-001..003 |
| REQ-VRF-001 | Verify candidates against normalized tokens, reconstruct maximal spans, map them to source ranges, merge overlaps, and deduplicate results deterministically. | M6 | golden/property | TC-VRF-001..005 |
| REQ-CLS-001 | Classify only verified exact-mode matches as Type 1 and renamed-mode matches as Type 2; never label similarity as plagiarism. | M6 | conformance | TC-CLS-001..003 |
| REQ-SCR-001 | Report fingerprint containment/Jaccard and verified token coverage separately; confidence is absent until calibrated on a declared dataset. | M6 | schema test | TC-SCR-001 |
| REQ-CLI-001 | Provide `scan`, `find-clones`, `compare`, `stats`, and `benchmark`, with human and stable JSON output and documented exit codes. | M7 | black-box | TC-CLI-001..006 |
| REQ-API-001 | Implement the versioned REST resources and schemas in `api-contracts.md`, including pagination, idempotency, and structured errors. | M8 | OpenAPI/contract | TC-API-001..010 |
| REQ-WEB-001 | Present scan state, clone groups, side-by-side evidence, filters, and explicit non-plagiarism language. | M9 | end-to-end/a11y | TC-WEB-001..003 |
| REQ-BEN-001 | Run reproducible synthetic and permissively licensed evaluation corpora and distinguish observed metrics from targets. | M10 | reproducibility | TC-BEN-001..002 |
| REQ-SEC-001 | Reject traversal and unsafe symlinks, binaries, oversized/deep inputs, and enforce CPU/memory/time/quantity limits. | M11 | adversarial | TC-SEC-001..007 |
| REQ-SEC-002 | Never log repository credentials or raw source; apply configurable retention and authenticated repository authorization. | M11 | security review | TC-SEC-008..010 |
| REQ-NFR-001 | Identical bytes, configuration, and versions must produce byte-identical ordered outputs across supported platforms. | M3 | reproducibility | TC-NFR-001 |
| REQ-NFR-002 | Target ≥20 KLOC/s scan throughput per worker, p95 search latency ≤2 s at 10M postings, and ≤250 MiB peak memory per 100 KLOC fixture; these are targets, not measurements. | M10 | benchmark | TC-NFR-002 |
| REQ-OBS-001 | Emit structured logs, metrics, and trace IDs without source text, secrets, or credential-bearing URLs. | M11 | inspection | TC-OBS-001 |
| REQ-EXT-001 | Permit future AST, PDG, MinHash/LSH, and embedding engines without changing the core ingestion or result contracts. | M12 | architecture test | TC-EXT-001 |

## Global acceptance rules

All outputs are ordered by stable identifiers and source position. Unsupported files are reported as skips, not silently ignored. Parser failure uses a declared adapter fallback or produces a diagnostic; it must not fabricate success. Requirements traceability is normative in [traceability-matrix.md](traceability-matrix.md).
