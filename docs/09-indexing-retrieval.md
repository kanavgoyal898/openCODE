# Indexing and Retrieval

The logical key is `(algorithm_version, normalization_version, mode, hash_u64)` and the posting contains repository/file revision, fragment, token position, and source mapping reference. Posting lists are ordered by fragment ID and position and segmented by tenant.

```text
for query fingerprint f:
  if document_frequency(f) <= max(500, 1% of indexed fragments):
    for posting in index[f]:
      candidate[posting.fragment].hashes.add(f)
      candidate[posting.fragment].pairs.add(query_pos, posting.pos)
retain candidates with >=3 distinct hashes; rank by shared count, then stable ID
```

SMALL queries bypass the three-hash threshold. Query budgets cap fingerprints, postings expanded, candidates, and wall time; truncation is explicit and cannot be called complete. Frequency statistics are version/mode/tenant scoped and transactionally updated. Retrieval optimizes recall and never emits final matches.

Index replacement is atomic per file revision and deletion cascades as specified in [data model](../specs/data-model.md). Phase two may partition postings by hash prefix/repository and cache bounded hot lists; MinHash/LSH remains an independent future retriever.
