# semantic-v1 Model Card

## Model identity

`opencode/feature-hash-code-embedding-v1` is the bundled offline baseline for experimental Type 4 retrieval. Its descriptor `feature-hash-v1|sha256|256|word-weight=4|max=2048` has checksum `sha256:cee9361b941ac964799b2c9a86fe69c3bf0e5707bfb6f5a5239adbd006b34fc8`. It produces a 256-dimensional L2-normalized vector from token kinds, syntax, identifier words, and AST node kinds, with deterministic signed feature hashing.

This is not a pretrained neural model. The `CodeEmbeddingModel` port is intentionally compatible with a separately packaged, license-reviewed, checksum-pinned pretrained provider, but openCODE does not silently download or execute third-party model code. Adding such a provider requires recording tokenizer, pooling, weights checksum, license, maximum length, evaluation, and a new algorithm version.

## Intended use and claim boundary

The vector index retrieves speculative candidates through cosine similarity. Every `semantic-v1` result is `candidate`, never `verified`, and states that embedding similarity is not semantic equivalence or plagiarism proof. It is intended to prioritize review and to validate the model/index contract before M14 multi-evidence verification.

## Inputs and truncation

The baseline consumes at most 2,048 parsed tokens and all bounded AST node kinds. Truncation is returned as `EMBEDDING_INPUT_TRUNCATED`. Invalid or unsupported source is rejected by normal ingestion before embedding. The implementation never executes analyzed source.

## Evaluation and limitations

The [M13 observed report](../../tests/benchmarks/results/m13-semantic-observed-macos-arm64.json) covers one syntactically diverse summation pair and two declared negatives, including a vocabulary-overlapping hard negative. It observed candidate precision/recall/F1 of 1.0 on only those three pairs. This tiny result does not establish general semantic recall, calibrated probability, pretrained-model quality, or semantic equivalence. Feature hashing is vocabulary-sensitive, collision-prone, language-distribution-sensitive, and weaker than a suitably governed pretrained code model.
