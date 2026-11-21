# CLI Contracts

Executable name: `opencode`. Commands never execute analyzed source. Diagnostics go to stderr; primary output goes to stdout.

| Command | Core options | Result |
|---|---|---|
| `scan PATH` | `--language`, `--mode`, `--exclude`, `--strict`, `--json` | ingestion/fingerprint summary and scan ID |
| `find-clones PATH` | `--type 1,2,3,4`, `--evidence-state`, `--min-tokens`, `--format text|json|sarif` | ordered clone groups/candidates with evidence |
| `compare FILE1 FILE2` | `--mode`, `--json` | verified spans and separate scores |
| `stats PATH` | `--json` | files, tokens, fingerprints, stop-fingerprints, skips |
| `benchmark [CORPUS]` | `--seed`, `--runs`, `--json`, `--output` | environment plus observed metrics |

Global flags are `--config FILE`, `--log-level`, `--no-color`, `--version`, and `--help`. Configuration precedence is flags > environment (`OPENCODE_*`) > project config > user config > defaults; effective non-secret configuration is included in debug logs.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | success, including a valid no-match result |
| 1 | completed with file-level skips/partial result |
| 2 | invalid usage or configuration |
| 3 | input/path/language error |
| 4 | analysis failure |
| 5 | persistence/service failure |
| 6 | resource/security limit exceeded |
| 130 | interrupted |

`--json` emits exactly one versioned JSON document and disables progress/color. It contains `schemaVersion`, `command`, `algorithmVersion`, `normalizationVersion`, `result`, `diagnostics`, and `timing`; paths are repository-relative and slash-normalized. SARIF is 2.1.0 and maps clone spans to related locations. JSON field removal or semantic change requires a schema version increment. See [test-cases.md](test-cases.md#cli-and-api).

Human and machine output label each result `verified`, `candidate`, or `rejected` and include detector/model versions, thresholds, source ranges, explanation codes, and limitations. Type 4 candidates are never printed under a “verified clones” heading.
