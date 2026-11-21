# ADR-003: Inverted Fingerprint Index

- Status: Accepted
- Date: 2026-11-22

## Context

Queries need high-recall candidate retrieval with positional evidence across files/repositories. Verification must remain a separate, strict phase.

## Decision

Use a tenant/version/mode/hash keyed inverted index with fragment and token-position postings in PostgreSQL for the MVP. Suppress hashes above the version-scoped document-frequency threshold for candidate generation, retain them as evidence, require three distinct shared hashes except SMALL streams, and enforce posting/candidate/time budgets.

## Consequences

The design is deterministic, inspectable, and transactionally consistent with revisions. Hot hashes can cause storage and latency pressure; frequency statistics and benchmark-driven partitioning mitigate this. Suppression weakens the theoretical Winnowing guarantee and must be reported.

## Alternatives

An external search engine adds operations and awkward positional semantics; an in-memory map lacks persistence/scale; LSH is probabilistic. Revisit partitioning or external storage only with M10 evidence and a compatibility plan.
