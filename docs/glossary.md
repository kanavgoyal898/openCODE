# Glossary

| Term | Definition |
|---|---|
| adapter | versioned language-specific detector/tokenizer implementing the common port |
| candidate | approximate retrieval result that is not yet a clone match |
| clone group | canonical set of related verified clone matches |
| confidence | calibrated estimate against a declared dataset; absent in MVP |
| evidence state | `candidate`, `verified`, or `rejected`; independent of clone category |
| fingerprint | selected versioned hash plus token position |
| fragment | bounded token/source region of a file revision |
| inverted index | map from fingerprint key to positional postings |
| k-gram | contiguous sequence of `k` normalized tokens |
| normalization | deterministic mapping from lexical tokens to canonical tokens |
| posting | occurrence of one fingerprint in a fragment and token position |
| source span | half-open UTF-8 byte range plus one-based line/column endpoints |
| stop-fingerprint | high-document-frequency hash excluded from candidate generation |
| Type 1/2/3/4 | exact-layout, renamed, modified, and semantic clone taxonomy |
| semantic candidate | Type 4 retrieval result lacking sufficient independent evidence for verification |
| verification | canonical-token comparison that turns candidates into evidence-backed matches |
| Winnowing | selection of rightmost minimum hash in each fixed-size window |

Score definitions and classification rules are normative in [algorithm contracts](../specs/algorithm-contracts.md).
