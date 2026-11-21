# Core package

`opencode_core` is the dependency-light standalone engine. It may depend on pinned parser libraries when M1 begins, but never on FastAPI, SQLAlchemy, Celery, PostgreSQL, Redis, or frontend code. Subpackages will be introduced in roadmap order: parsers, normalization, fingerprinting, indexing, retrieval, matching, and classification.

The package exposes package and algorithm version constants separately so a release cannot silently reinterpret persisted fingerprints.
