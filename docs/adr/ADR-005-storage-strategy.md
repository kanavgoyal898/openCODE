# ADR-005: Storage Strategy

- Status: Accepted; hash representation resolved at M8
- Date: 2026-11-22

## Context

Metadata, revisions, positional postings, scans, matches, and evidence need transactional consistency and cascading deletion. Private source may need temporary retention but should not sit in logs or broad-access database fields.

## Decision

Use PostgreSQL as relational system of record and a restricted encrypted blob abstraction for optional source bytes. Replace derived data atomically per file revision; use foreign keys/cascades and a deletion outbox for blobs. Apply forward-only expand/contract migrations and restore-tested backups.

Store unsigned 64-bit hashes in signed PostgreSQL `BIGINT` through a reversible order-preserving sign-bit transform: XOR the unsigned value with `2^63`, then interpret the bits as two's-complement signed. Equality and ordering use the compact native B-tree type; application boundary functions enforce ranges and reverse the mapping. The initial migration fixes this representation.

## Consequences

Transactions prevent stale active postings and PostgreSQL simplifies early operations. Posting volume may require bulk copy and later partitioning. Blob deletion is eventually completed but query visibility ends immediately. The `BIGINT` transform adds explicit conversion at persistence boundaries but avoids variable-width numeric index overhead.

## Alternatives

Storing source inline broadens exposure; object storage for postings weakens point lookup/transactions; an external search store adds dual-write consistency. These remain rejected until benchmark evidence changes the tradeoff.
