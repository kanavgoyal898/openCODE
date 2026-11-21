# Language Adapter Contract

## Interface and output

Adapters implement `LanguageAdapter` from [architecture.md](architecture.md). Inputs are UTF-8 bytes after BOM removal; invalid UTF-8 produces `INVALID_ENCODING`. Tokens must be lexical, ordered, non-overlapping, and carry exact byte and one-based line/column spans. Newline is LF for coordinate calculation after CRLF normalization, while byte spans refer to original bytes.

| Adapter | Extensions | Parser strategy | Identifier support | Fallback |
|---|---|---|---|---|
| Python | `.py`, `.pyi` | tree-sitter grammar pinned by lockfile | Unicode XID per grammar | tree-sitter error-tolerant lexical leaves |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | tree-sitter JavaScript | ECMAScript identifiers/escapes | same |
| TypeScript | `.ts`, `.tsx`, `.mts`, `.cts` | tree-sitter TypeScript/TSX | ECMAScript identifiers/escapes | same |
| Java | `.java` | tree-sitter Java | Java identifier rules | same |

Language detection order is explicit override, recognized extension, then bounded content heuristics. Ambiguity is `UNSUPPORTED_LANGUAGE`, never a guess. Grammar name and checksum are part of adapter version metadata.

## Token categories

Adapters map grammar-specific leaves to `keyword`, `identifier`, `operator`, `punctuation`, `string`, `number`, `boolean`, `null`, or `other`. They omit comments, whitespace, indentation layout tokens, and synthetic parser recovery nodes. Python `INDENT`/`DEDENT` are represented as punctuation only when needed to distinguish suite boundaries; semantically insignificant semicolons are retained because the MVP is lexical.

## Failure and safety

Parsing never loads modules, expands macros, invokes compilers, follows imports, or executes hooks. A file with error nodes may be indexed if lexical coverage is ≥90%; the result records `degraded=true` and diagnostic counts. Below that threshold it is skipped. Adapters enforce the common byte/token/depth/time limits and stream tokens where supported.

## Extension checklist

A new adapter needs grammar provenance/license, pinned checksum, detector rules, category mapping, Unicode and literal fixtures, malformed-input tests, coordinate golden tests, resource-limit tests, and a normalization compatibility declaration. Passing [TC-LNG-001](test-cases.md#language-and-normalization) equivalents is mandatory.
