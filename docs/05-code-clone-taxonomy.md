# Code Clone Taxonomy

| Type | Meaning | MVP detection | Claim boundary |
|---|---|---|---|
| Type 1 | same tokens after layout/comment normalization | verified `exact` stream equality | lexical identity only |
| Type 2 | Type 1 plus consistent identifier/literal policy normalization | verified `renamed` equality and non-equal exact span | conservative renamed clone |
| Type 3 | statements/tokens added, removed, changed, or safely reordered | AST fingerprints + approximate retrieval + structural/token verification | verified only after alignment thresholds |
| Type 4 | similar functionality despite syntax/structure differences | embedding candidates; control/data-flow or PDG multi-evidence verification | embeddings alone remain speculative |

A clone is a contiguous verified span meeting the minimum-token rule. Boilerplate and high-frequency fingerprints can create candidates, so verification, frequency evidence, and context remain visible. Generated code may be excluded or labeled and never silently mixed with authored-code metrics. Repeated matches are canonicalized into groups by version, type, and normalized span signature.

Fingerprint overlap is retrieval evidence; token coverage/Jaccard describe verified lexical overlap; structural scores describe versioned AST alignment; embedding cosine similarity is candidate-retrieval evidence. Confidence requires held-out calibration. None proves plagiarism or universal semantic equivalence. Classification rules are normative in [algorithm contracts](../specs/algorithm-contracts.md) and [detector contracts](../specs/detection-engines.md).
