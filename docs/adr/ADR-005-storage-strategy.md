# ADR-005: Storage Strategy

- Status: Accepted with one implementation choice deferred to M4
- Date: 2026-11-22

## Context

Metadata, revisions, positional postings, scans, matches, and evidence need transactional consistency and cascading deletion. Private source may need temporary retention but should not sit in logs or broad-access database fields.

## Decision

Use PostgreSQL as relational system of record and a restricted encrypted blob abstraction for optional source bytes. Replace derived data atomically per file revision; use foreign keys/cascades and a deletion outbox for blobs. Apply forward-only expand/contract migrations and restore-tested backups.

Before the M4 schema freezes, benchmark two lossless unsigned-hash representations: `numeric(20,0)` and signed `bigint` with an explicit order-preserving unsigned mapping. Record the selected representation in a migration and update this ADR; no application code may assume one beforehand.

## Consequences

Transactions prevent stale active postings and PostgreSQL simplifies early operations. Posting volume may require bulk copy and later partitioning. Blob deletion is eventually completed but query visibility ends immediately. The bounded deferred hash representation is tracked as RSK-011.

## Alternatives

Storing source inline broadens exposure; object storage for postings weakens point lookup/transactions; an external search store adds dual-write consistency. These remain rejected until benchmark evidence changes the tradeoff.
