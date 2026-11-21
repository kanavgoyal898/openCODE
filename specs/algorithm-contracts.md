# Algorithm Contracts

## Version `fp-v1`

| Parameter | Value |
|---|---|
| Token k-gram `k` | 25 normalized tokens |
| Winnowing window `w` | 4 consecutive k-gram hashes |
| Guarantee threshold | `t = k + w - 1 = 28` tokens |
| Hash | unsigned 64-bit polynomial rolling hash modulo `2^64` |
| Base | 1,000,003 |
| Token code | first 64 bits of SHA-256 over UTF-8 `kind + NUL + canonical` |
| Tie rule | rightmost minimum; emit only when selected position changes |
| Modes | `exact`, `renamed` |

All arithmetic wraps modulo `2^64`; bytes are serialized big-endian as 16 lowercase hex digits. Collision equality is never proof of a clone.

```text
codes = token_codes(tokens)
if len(codes) < k: return one SMALL fingerprint = SHA256(codes)[0:8] at position 0
h = rolling_hash(codes[0:k], base)
hashes = [h]
for i in 1..len(codes)-k:
    h = (h - codes[i-1] * base^(k-1)) * base + codes[i+k-1] mod 2^64
    hashes.append(h)
for each window hashes[j:j+w]:
    p = greatest index having the minimum unsigned hash
    emit (hashes[p], p) if p differs from last emitted position
```

For fewer than `k` tokens, the namespace-tagged SMALL fingerprint supports exact candidate retrieval only; verification still compares full streams. Empty streams yield no fingerprint.

## Detection guarantee

Under identical `norm-v1` streams, complete k-gram construction, no frequency suppression, and no hash collision, every common contiguous region of at least `t=28` tokens selects at least one common fingerprint. The guarantee does not apply across parser modes, version changes, ignored boilerplate, truncated inputs, or frequency suppression; it says nothing about semantic equivalence.

## Retrieval and verification

Postings are keyed by version/mode/hash. Hashes occurring in more than `max(500, 0.01 * indexed_fragments)` fragments are stop-fingerprints for candidate generation but remain available for evidence. Candidates require at least three shared selected hashes, except SMALL queries, and are ranked by shared distinct hashes then stable ID.

Verifier groups `(query_position - candidate_position)` runs, expands seeds by token equality, merges spans whose gap is ≤3 tokens, and discards spans shorter than 28 tokens (SMALL: entire stream must match). It reports:

- `fingerprint_jaccard = |Fq∩Fc| / |Fq∪Fc|` over distinct non-stop hashes;
- `query_coverage = matched_query_tokens / query_tokens`;
- `candidate_coverage = matched_candidate_tokens / candidate_tokens`;
- `token_jaccard = matched_union / token_union` after interval merging.

No field is called probability. Type 1 requires a verified exact-mode span; Type 2 requires renamed-mode equality and failure of exact-mode equality over the same span. Future AST/PDG/embedding scores use separate versioned evidence kinds.

## Determinism and collision defense

Sort postings and results lexicographically by stable IDs and positions. Verification compares canonical token sequences, so unequal sequences sharing a 64-bit hash are rejected. Test vectors live conceptually in [test-cases.md](test-cases.md); any parameter or serialization change requires a new algorithm version.
