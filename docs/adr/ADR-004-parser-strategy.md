# ADR-004: Parser Strategy

- Status: Accepted
- Date: 2026-11-22

## Context

Four languages require consistent token categories and coordinates, malformed-input tolerance, Unicode support, and no source execution. Full compiler front ends are heavy and language-specific; regex tokenizers are unsafe and inaccurate.

## Decision

Use pinned tree-sitter grammars behind versioned `LanguageAdapter` ports. Map lexical leaves to common categories, preserve original UTF-8 byte and line/column spans, and permit error-tolerant output only at ≥90% lexical coverage with a degraded diagnostic. Never resolve imports, invoke build systems, expand macros, or execute source.

## Consequences

Tree-sitter offers incremental, error-tolerant parsing and uniform integration, but grammar updates can change streams and require adapter-version/golden updates. Some semantic identifier roles are approximate; `norm-v1` stays conservative.

## Alternatives

Native compiler parsers improve semantic detail but expand attack surface and operational dependencies. Pure lexical scanners reduce dependencies but mishandle syntax/Unicode. ANTLR duplicates grammar maintenance. AST extensions may add compiler-derived adapters later behind separate versions.
