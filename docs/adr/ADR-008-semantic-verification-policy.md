# ADR-008: Conservative Semantic Verification Policy

- Status: Accepted
- Date: 2026-11-22
- Decision owners: openCODE maintainers

## Context

Embedding proximity is useful for retrieval but can join fragments that share vocabulary rather than behavior. Universal program equivalence is undecidable in the general case, and analyzed repositories may contain dynamic evaluation, reflection, external I/O, or hostile code. M14 needs a useful verified state without overstating what the evidence proves.

## Decision

`semantic-v2` is an opt-in promotion policy layered on `semantic-v1` retrieval. Promotion requires all of the following:

1. the pinned embedding candidate passes its cosine threshold;
2. language-neutral control-flow feature similarity meets the configured threshold;
3. normalized def-use feature similarity independently meets the threshold;
4. the combined PDG-style feature view meets the threshold; and
5. neither fragment contains a recognized unsupported dynamic, reflection, process, network, or file-I/O construct.

An empty feature set is absence of evidence and scores zero. The PDG-style score is corroborating composition, not a claim of a complete formal program-dependence graph. CFG and def-use agreement are the two required non-embedding signals. Results retain the embedding limitation even after promotion and mean “verified under this bounded policy,” not mathematical equivalence.

Behavioral comparison is a separate, optional evidence source. It is disabled by default and accepts only an approved harness. The local runner requires explicit enablement and an attestation that its surrounding container or orchestrator has removed network access. It then uses isolated Python startup, an empty environment, a disposable working directory, and CPU, address-space, file-size, descriptor, process, output, and wall-time bounds. Python flags and resource limits do not themselves provide a network or syscall sandbox; production must supply those boundaries. Passing inputs supports only the tested domain and does not imply universal equivalence.

## Consequences

- Embedding-only and unsupported matches remain candidates.
- Verification is deterministic, explainable, versioned, and conservative, but may have low recall.
- The initial static representations are deliberately shallow and must not be described as compiler-grade proofs.
- A future behavioral service or richer interprocedural analysis requires a new evidence version and evaluation.

## Alternatives

- Embedding threshold alone was rejected because it cannot establish semantic equivalence.
- Behavioral execution by default was rejected because repository-controlled code is hostile input.
- A single combined score was rejected because it hides missing independent evidence.
