# Code Clone Taxonomy

| Type | Meaning | MVP detection | Claim boundary |
|---|---|---|---|
| Type 1 | same tokens after layout/comment normalization | verified `exact` stream equality | lexical identity only |
| Type 2 | Type 1 plus consistent identifier/literal policy normalization | verified `renamed` equality and non-equal exact span | conservative renamed clone |
| Type 3 | statements/tokens added, removed, or changed | future gap-aware/AST method | not an MVP claim |
| Type 4 | semantically similar implementation | future PDG/embedding + calibrated evaluation | never inferred from lexical score |

A clone is a contiguous verified span meeting the minimum-token rule. Boilerplate and high-frequency fingerprints can create candidates, so verification, frequency evidence, and context remain visible. Generated code may be excluded or labeled and never silently mixed with authored-code metrics. Repeated matches are canonicalized into groups by version, type, and normalized span signature.

Fingerprint overlap is retrieval evidence; token coverage/Jaccard describe verified lexical overlap; structural similarity requires an AST/graph method; confidence requires held-out calibration. None proves plagiarism. Classification rules are normative in [algorithm contracts](../specs/algorithm-contracts.md).
