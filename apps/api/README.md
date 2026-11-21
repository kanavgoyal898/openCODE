# API application

The M8 FastAPI adapter implements [`specs/api-contracts.md`](../../specs/api-contracts.md) over the standalone engine and SQLAlchemy persistence. It contains transport, authorization, idempotency, pagination, and transaction orchestration—not tokenization or matching algorithms.

Production uses `OPENCODE_DATABASE_URL=postgresql+psycopg://...` and Alembic migrations. Trusted local paths must fall under the configured allowlist. Hosted mode requires an OIDC-compatible bearer validation adapter; the built-in static token option is intended for integration and private deployments.
