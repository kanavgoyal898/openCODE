# Tokenization and Normalization

`norm-v1` consumes adapter tokens and preserves the source-span map. Whitespace, comments, BOM, and layout-only tokens are dropped. Keywords/operators/punctuation retain normalized spelling. Unicode identifiers are decoded, Unicode-normalized to NFC for comparison, and their original source spans remain unchanged; invalid encoding is rejected.

| Token | `exact` | `renamed` |
|---|---|---|
| identifier | NFC spelling | deterministic placeholder by lexical role/scope and first occurrence (`ID_LOCAL_0`, `ID_MEMBER_0`, …) |
| string | decoded category plus original lexeme hash | `STR` (prefix/template kind retained) |
| integer/float | canonical numeric spelling where lossless | `NUM_INT` / `NUM_FLOAT` |
| boolean/null | keyword retained | keyword retained |
| keyword/operator/punctuation | canonical spelling | same |

Property/member names are normalized separately from locals; language keywords never become identifiers. Escape-equivalent literals canonicalize only when the parser proves equivalent value. Generated files detected by configured path/header rules are labeled and excluded by default. Error-tolerant parsing requires ≥90% lexical coverage. Functions below 25 tokens use the SMALL contract; repeated boilerplate is controlled by stop-fingerprints, not erased from verification.

Token boundaries and adapter obligations are in [language adapters](../specs/language-adapters.md); any policy change creates `norm-v2`.
