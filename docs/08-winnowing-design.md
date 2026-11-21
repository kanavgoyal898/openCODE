# Winnowing Design

For normalized token codes `c_i`, the k-gram hash is `H_i = Σ(c_{i+j} b^(k-1-j)) mod 2^64`, with `k=25`, `b=1,000,003`. The next hash removes the outgoing high-order term, multiplies by `b`, and adds the incoming code. Unsigned comparison is mandatory.

```text
for each four-hash window:
  choose the greatest position whose hash equals the window minimum
  emit only when that absolute position differs from the last emission
```

Rightmost tie-breaking prevents repeated emission while remaining deterministic. With a shared normalized substring of at least `t=k+w-1=28` tokens, identical version/configuration, complete windows, no suppression, and no collision, at least one selected fingerprint is shared. This guarantee does not imply candidate survival after frequency policy and does not imply a clone until token verification.

Short non-empty streams use a namespace-separated SHA-256-derived SMALL fingerprint and require full-stream verification. Fixed vectors must cover wraparound, rightmost ties, repeated hashes, lengths 0/24/25/28, and equivalence to naive recomputation. See [formal contract](../specs/algorithm-contracts.md).
