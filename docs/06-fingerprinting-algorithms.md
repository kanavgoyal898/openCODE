# Fingerprinting Algorithm Survey

| Method | Foundation / complexity | Invariance and use | Limits / false positives / retrieval |
|---|---|---|---|
| Cryptographic file hash | SHA-256; O(n) time, O(1) stream space | exact bytes, integrity/dedup | no edit tolerance; hash lookup |
| Token normalization | lexer/parser mapping; O(T) | layout/comments, selected renames | information loss/boilerplate; downstream index |
| Rabin–Karp | polynomial rolling hash mod `2^64`; O(T) | equal k-token regions | collisions/repetition; verify tokens |
| Winnowing | minimum per window; O(T) deque, O(w) space | samples local matches with threshold guarantee | boundary/tie/frequency effects; inverted index |
| Inverted index | hash→posting list; build O(P), query O(|F|+postings) | fast exact fingerprint lookup | hot hashes/storage; stop policy |
| MinHash | min-wise estimators; O(pT) | approximate set Jaccard | loses order/small sets; LSH bands |
| LSH | bucketed signatures; sublinear expected candidates | approximate neighbor retrieval | probabilistic misses/tuning |
| AST fingerprints | subtree hashes; O(nodes) typical | layout and some syntax variation | parser/language coupling, common subtrees |
| PDG | control/data-flow graph matching; often superlinear/NP-hard variants | structural/semantic relations | build/toolchain cost and alias imprecision |
| Code embeddings | learned vector mapping; model-dependent | semantic neighborhoods | opacity, drift, bias, hardware; ANN index |

## MVP decision and pseudocode

```text
tokens = adapter.tokenize(bytes)
for mode in [exact, renamed]:
  normalized = norm_v1(tokens, mode)
  hashes = rolling_kgrams(normalized, k=25, base=1000003)
  fingerprints = rightmost_minima(hashes, window=4)
  index(version="fp-v1", mode, fingerprints)
```

The MVP combination is deterministic, explainable, position-preserving, and efficiently indexable. Cryptographic hashes still identify content/config. Alternatives remain versioned plugins; mixing their scores is forbidden without calibration. Formal math, tie rules, guarantee assumptions, and collision defense are in [algorithm contracts](../specs/algorithm-contracts.md).
