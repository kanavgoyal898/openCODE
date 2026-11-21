# ADR-006: Pluggable Clone Detection Engines

- Status: Accepted
- Date: 2026-11-22

## Context

The complete project must detect Type 1 exact, Type 2 renamed, Type 3 near-miss, and Type 4 semantic clones. These categories require different indexes, thresholds, verification methods, evaluation datasets, and claim strength. A single blended score would be difficult to reproduce and could misrepresent embedding proximity as semantic equivalence.

## Decision

Create four independent implementations—`ExactCloneDetector`, `TokenCloneDetector`, `StructuralCloneDetector`, and `SemanticCloneDetector`—behind one versioned `CloneDetector` port. Retrieval and verification remain separate in every engine. Results carry `candidate`, `verified`, or `rejected` state, engine-specific scores/evidence, source spans, versions, thresholds, and limitations.

Type 3 uses language-neutral AST fingerprints plus approximate retrieval, then bounded structural and token alignment. Type 4 initially uses pinned embeddings only for candidate retrieval. Promotion to verified Type 4 requires an approved multi-evidence policy with non-embedding program-analysis signals; optional behavioral checks are explicit, disabled by default, and run in a hardened sandbox.

Aggregation canonicalizes and deduplicates fragment pairs but retains all engine evidence. It never converts a candidate to verified or mixes incomparable scores into an undocumented scalar.

## Consequences

The architecture supports independent evolution and honest evidence, at the cost of multiple indexes, larger evaluation corpora, and more complex result schemas. Model/grammar/index upgrades require new versions and evaluation. Type 4 verified recall will initially be limited because unsupported dynamic behavior remains candidate-only.

## Alternatives

A single detector was rejected because lexical, structural, and learned similarities have incompatible semantics. Embedding-only Type 4 classification was rejected as insufficient evidence. Always-on behavioral execution was rejected because untrusted source, incomplete inputs, nondeterminism, and sandbox risk conflict with the default non-execution security posture.
