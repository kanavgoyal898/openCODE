# Database Design

PostgreSQL stores metadata, versioned algorithms, scan state, fragments, postings, matches, and evidence; a restricted blob adapter optionally stores source bytes. UUIDv7 keys improve locality, SHA-256 identifies content/config, and every tenant-owned table carries or derives tenant scope.

```mermaid
erDiagram
  REPOSITORY ||--o{ SOURCE_FILE : contains
  SOURCE_FILE ||--o{ FILE_REVISION : versions
  FILE_REVISION ||--o{ FRAGMENT : splits
  FRAGMENT ||--o{ POSTING : has
  FINGERPRINT ||--o{ POSTING : indexes
  ALGORITHM_VERSION ||--o{ FINGERPRINT : defines
  REPOSITORY ||--o{ SCAN_JOB : scans
  SCAN_JOB ||--o{ CLONE_GROUP : produces
  CLONE_GROUP ||--o{ CLONE_MATCH : groups
  CLONE_MATCH ||--o{ MATCH_EVIDENCE : explains
```

Per-file replacement stages computed data outside the database, then locks the file and atomically activates one complete revision. Foreign-key cascades prevent orphan postings; algorithm versions are restricted while referenced. Repository deletion immediately hides rows, transactionally removes relational children, and emits an idempotent blob-deletion event.

Initial indexes cover tenant/repository paths, active revisions, fingerprint/hash posting lookup, scan status, and clone range queries. Partitioning is deferred until benchmark evidence warrants hash-prefix or tenant partitions. Forward-only expand/contract migrations and restore drills are mandatory. The column-level normative contract is [data-model.md](../specs/data-model.md).
