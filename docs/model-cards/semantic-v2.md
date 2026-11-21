# semantic-v2 Evidence Card

## Identity and scope

`semantic-v2` is the M14 promotion policy, not a new embedding model. It consumes candidates from the pinned `opencode/feature-hash-code-embedding-v1` baseline described in [semantic-v1](semantic-v1.md), then compares language-neutral CFG shape, normalized def-use distance classes, and a combined PDG-style feature set. The default threshold is 0.70 for each non-embedding score.

## Claim boundary

A `verified` result means the pair satisfied the bounded policy in [ADR-008](../adr/ADR-008-semantic-verification-policy.md). It does not prove universal semantic equivalence, plagiarism, authorship, or behavior outside represented constructs. Empty static evidence never counts as agreement. Dynamic evaluation, reflection, process creation, network or file I/O, and other recognized unsupported constructs force candidate-only status.

## Behavioral evidence

The optional harness runner is disabled by default. Its `network_isolated` input is an external isolation attestation, not an in-process network control. Production callers must place it in a disposable no-network, syscall-restricted sandbox. Successful runs establish evidence only for approved inputs and observed outputs; M14 does not use behavioral success to bypass the static promotion gates.

## Evaluation

The [M14 observed report](../../tests/benchmarks/results/m14-verified-observed-macos-arm64.json) covers one cross-language summation positive and two negatives, including a vocabulary/control-shape hard negative and a dynamic-evaluation fragment. Embedding candidate retrieval observed precision 0.50 and recall 1.00. Static promotion observed precision, recall, and F1 of 1.00 for the verified state. Five repetitions observed p95 search latency of 2.46 ms and peak traced Python memory of 103,957 bytes on 16 lines. This tiny synthetic corpus validates the contract only and does not establish broad semantic quality or production-scale performance.
