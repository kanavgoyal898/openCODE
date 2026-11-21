# CLI Specification

`opencode` is a thin adapter over the same application/core services as REST. Human output favors concise tables and source ranges; `--json` emits one stable versioned document without progress or ANSI escapes; clone discovery may emit SARIF 2.1.0.

Examples:

```console
opencode scan ./repository --mode exact --mode renamed
opencode find-clones ./repository --type 1,2 --format sarif
opencode compare file1.py file2.py --json
opencode stats ./repository
opencode benchmark --seed 20261122 --runs 5 --output results.json
```

Paths in machine output are root-relative slash paths. stdout contains only the requested report, stderr contains diagnostics, and a no-match is exit 0. Partial scans are exit 1; invalid input, analysis, service, and resource-limit failures have distinct codes. Interruptions clean temporary state and return 130. The full option, JSON, precedence, and exit-code contract is [cli-contracts.md](../specs/cli-contracts.md).
