# CLI package

The M7 command-line adapter calls the public standalone engine and remains usable without the API server, PostgreSQL, Redis, Docker, or web application. Its normative contract is [`../../specs/cli-contracts.md`](../../specs/cli-contracts.md).

```console
opencode scan ./repository
opencode find-clones ./repository --format json
opencode compare first.py second.py
opencode stats ./repository
opencode benchmark ./repository --runs 5 --output benchmark.json
```

`--json` writes one versioned document to stdout. Diagnostics use stderr, a valid no-match exits 0, partial scans exit 1, and input, analysis, service, and resource failures retain distinct codes.
