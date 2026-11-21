# API Specification

The REST API is resource-oriented JSON under `/api/v1`. It supports repositories, asynchronous scans, clone list/detail, synchronous bounded snippet search, and health/readiness. Hosted deployments require OIDC bearer authentication and tenant authorization; trusted local mode may disable authentication only on loopback.

POST operations use idempotency keys. Lists use opaque signed cursors and deterministic order. Errors have stable codes, a safe message, request ID, and bounded structured details. Raw source and credential references are never returned in list objects. Large repository analysis is always asynchronous.

The normative endpoint/schema table is [api-contracts.md](../specs/api-contracts.md). OpenAPI 3.1 is generated from implementation schemas, linted, diffed for breaking changes, and exercised by consumer/provider contract tests. Versioning policy: additive optional fields are compatible; removed fields, changed meaning/type, or relaxed security require a new API/schema version and migration window.
