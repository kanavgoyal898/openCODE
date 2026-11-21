# Clone Detection Engine Contracts

This specification makes all four clone categories required while preserving phased delivery and evidence integrity.

## Common interface

```python
class CloneDetector(Protocol):
    detector_id: str
    category: Literal["type1", "type2", "type3", "type4"]
    algorithm_version: str
    def retrieve(self, query: CodeFragment, config: DetectorConfig) -> Iterable[Candidate]: ...
    def verify(self, candidate: Candidate, config: DetectorConfig) -> DetectionResult: ...
```

`DetectorConfig` is immutable and records threshold, retrieval budget, model/grammar versions, enabled evidence sources, and resource limits. `DetectionResult` contains category, `candidate|verified|rejected` state, source ranges, per-engine scores, evidence records, explanation codes, versions, thresholds, and limitations. Each engine has independent configuration and index schema.

| Engine | Category | Retrieval | Verification | Allowed final state |
|---|---|---|---|---|
| `ExactCloneDetector` | Type 1 | exact-mode Winnowing index | exact normalized-token spans | verified/rejected |
| `TokenCloneDetector` | Type 2 | renamed-mode Winnowing index | renamed alignment plus exact inequality | verified/rejected |
| `StructuralCloneDetector` | Type 3 | weighted AST subtree fingerprints plus MinHash/LSH | AST edit/containment score and token-sequence alignment | verified/rejected |
| `SemanticCloneDetector` | Type 4 | versioned embeddings in an ANN/vector index | multi-evidence analysis; embeddings alone never verify | candidate/verified/rejected |

## Type 3 contract (`struct-v1`)

Adapters produce language-neutral AST nodes with stable kinds, ordered children, source spans, and normalized leaf roles. Hash-consed subtree fingerprints exclude trivia and raw identifier spelling. A weighted multiset MinHash signature supports approximate retrieval; LSH parameters are versioned and evaluation must establish candidate recall.

Verification combines: normalized tree-edit similarity, matched-statement coverage, token local alignment, and control-dependence consistency. Default verification requires structural similarity ≥0.80, aligned token coverage ≥0.65 on both fragments, and at least three matched statements; thresholds are configurable and always returned. Reordering credit is allowed only when conservative def-use/control checks find no dependency path between reordered statements. Otherwise order changes lower the score.

```text
candidate = LSH(AST_subtree_signature(query))
mapping = bounded_weighted_tree_alignment(query.ast, candidate.ast)
tokens = local_token_alignment(query.tokens, candidate.tokens)
if structure >= threshold and both token coverages >= threshold:
    return verified(TYPE3, edits=mapping.edits, alignment=tokens)
return rejected
```

Evidence identifies added/removed/modified/moved nodes, aligned token ranges, structural features, and source spans. Time/space budgets may produce an explicit truncated candidate, never a verified result.

## Type 4 contract (`semantic-v1` experimental, `semantic-v2` verified)

`semantic-v1` embeds function/method fragments with a pinned model, tokenizer, pooling, truncation policy, license, checksum, and model card. Cosine similarity through an ANN index retrieves candidates. Results are always `candidate`, carry the raw similarity and retrieval rank, and state that similarity is not semantic equivalence.

`semantic-v2` may promote a candidate to `verified` only when an approved evidence policy supplies at least two independent non-embedding signals, including control/data-flow or program-dependence similarity. Optional behavioral comparison is disabled by default, runs only with explicit authorization inside a no-network, resource-limited sandbox, uses generated/approved inputs, and records coverage and observable outputs. Passing tests supports only the tested input domain.

The implemented `semantic-v2` policy requires CFG-shape and normalized def-use similarity independently, plus a corroborating combined PDG-style feature score; every score must meet the configured threshold (default 0.70). Empty feature sets score zero rather than agreement. The PDG-style representation is a bounded feature composition, not a complete formal PDG. Dynamic evaluation, reflection, process/network/file I/O, and recognized unsupported constructs prevent promotion. CLI `--verify-semantic` and API/worker mode `semantic-verified` are the only promotion switches; neither enables behavioral execution.

No engine may claim universal program equivalence. Native code, dynamic evaluation, reflection, external I/O, nondeterminism, or unsupported constructs force candidate-only or rejected status.

## Aggregation and metrics

Aggregation canonicalizes fragment pairs and ranges. When engines overlap, it retains all evidence and reports the strongest verified category without discarding lower-category proof; Type 4 candidates never override verified Type 1–3 results. Metrics are computed per category and evidence state on disjoint development and held-out datasets. Dataset, labeling rule, versions, thresholds, and confidence intervals accompany every result.
