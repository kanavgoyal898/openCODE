# Data Model Contract

PostgreSQL is the system of record. IDs are UUIDv7; timestamps are UTC `timestamptz`; checksums are lowercase SHA-256 hex.

| Table | Key and important columns | Constraints / indexes | Delete behavior |
|---|---|---|---|
| `repositories` | `id`, `tenant_id`, `name`, `origin_redacted`, `retention_policy` | unique `(tenant_id,name)` | cascades all children |
| `source_files` | `id`, `repository_id`, `logical_path` | unique `(repository_id,logical_path)`; path index | cascade |
| `file_revisions` | `id`, `source_file_id`, `content_sha256`, `byte_size`, `language`, `adapter_version` | unique `(source_file_id,content_sha256,adapter_version)` | cascade derived rows |
| `fragments` | `id`, `file_revision_id`, `kind`, token/source bounds | bounds check; index revision/range | cascade |
| `algorithm_versions` | `id`, `fingerprint_version`, `normalization_version`, `config_json`, `config_sha256` | unique config checksum; immutable | restrict while referenced |
| `fingerprints` | `id`, `algorithm_version_id`, `mode`, `hash_u64` | unique `(algorithm_version_id,mode,hash_u64)` | restrict |
| `fingerprint_postings` | `fingerprint_id`, `fragment_id`, `token_position` | PK all three; indexes `(fingerprint_id,fragment_id)` and `(fragment_id)` | cascade with fragment |
| `scan_jobs` | `id`, `repository_id`, `algorithm_version_id`, status, counts, error | idempotency key unique per tenant | retain per policy/cascade repo |
| `clone_groups` | `id`, `scan_job_id`, `clone_type`, stable signature | unique `(scan_job_id,signature)` | cascade |
| `clone_matches` | `id`, `clone_group_id`, left/right fragment and ranges, scores | canonical left ID < right ID; range indexes | cascade |
| `match_evidence` | `id`, `clone_match_id`, `kind`, `version`, `payload_json` | index match/kind | cascade |

`hash_u64` is stored as signed `bigint` using the reversible order-preserving sign-bit transform fixed by ADR-005 and the initial migration. JSON payloads are schema-versioned and bounded.

## Transaction boundaries

Fingerprint computation occurs outside a transaction into a bounded staging stream. One transaction locks the source file, upserts the revision, deletes derived rows for the superseded active revision, bulk-inserts fragments/postings, changes `source_files.active_revision_id`, and marks the file successful. A final transaction derives scan outcome. Failure rolls back the entire file replacement, so stale postings cannot remain active.

Repository deletion is a soft-delete authorization event followed by a transactional hard delete of relational rows and an idempotent blob-deletion outbox event. Queries filter deleted repositories immediately. Retrying the outbox is safe.

## Migrations and concurrency

Forward-only numbered migrations run before workers of the new version. Expand/contract changes support rolling deployment. Workers use optimistic scan state transitions and `SELECT … FOR UPDATE` per source file; duplicate revision ingestion converges via uniqueness constraints. Backups must be restore-tested. See [../docs/11-database-design.md](../docs/11-database-design.md).
