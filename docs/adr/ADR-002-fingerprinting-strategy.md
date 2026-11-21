# ADR-002: MVP Fingerprinting Strategy

- Status: Accepted
- Date: 2026-11-22

## Context

The MVP must explain evidence, preserve positions, detect Type 1/2 clones, and support efficient exact retrieval without claiming semantic equivalence.

## Decision

Adopt versioned token normalization, 25-token unsigned 64-bit polynomial rolling hashes, rightmost-minimum Winnowing with four-hash windows, and mandatory canonical-token verification. Maintain exact and renamed streams. Use namespace-separated short-stream fingerprints and record `norm-v1`/`fp-v1` with every set.

## Consequences

Shared normalized regions of at least 28 tokens receive the documented conditional guarantee. Hash collisions and boilerplate remain possible candidates but cannot pass unequal-token verification. Identifier/literal policy may trade recall against false positives and therefore requires corpus evaluation.

## Alternatives

File SHA-256 is retained for identity but lacks edit tolerance. MinHash/LSH loses positional guarantees; AST/PDG and embeddings add parser/model complexity and different evidence semantics. They may become independent versioned retrievers, never silent replacements. Full details: [algorithm contracts](../../specs/algorithm-contracts.md).
