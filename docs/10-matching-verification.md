# Matching and Verification

Candidate evidence is grouped by diagonal `query_position - candidate_position`. Seeds are expanded left/right by canonical-token equality, nearby spans (gap ≤3) are merged when the intervening tokens verify, and spans below 28 tokens are discarded except full SMALL equality. Intervals are unioned before scores are calculated.

```text
verify(candidate):
  reject incompatible versions
  seeds = stable_sort(shared_position_pairs)
  spans = expand_equal_tokens(seeds)
  spans = merge_verified_gaps(spans, max_gap=3)
  spans = maximal_nonredundant_intervals(spans)
  map token endpoints through source-span table
  return spans >= minimum length
```

Pairs are canonicalized by stable fragment ID; contained duplicates with identical type/evidence are removed; overlapping matches are clustered into a stable clone-group signature. Exact equality produces Type 1. Renamed equality only produces Type 2 if exact equality fails over that span. No match returns an empty collection, not an error.

Fingerprint Jaccard, query/candidate token coverage, and token Jaccard are separate reproducible fields. Structural similarity and calibrated confidence are absent in MVP. Collision defense always compares tokens. See [algorithm contract](../specs/algorithm-contracts.md) and [taxonomy](05-code-clone-taxonomy.md).
