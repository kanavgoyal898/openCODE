# Core package

`opencode_core` is the dependency-light standalone engine. It may depend on pinned parser libraries when M1 begins, but never on FastAPI, SQLAlchemy, Celery, PostgreSQL, Redis, or frontend code. Subpackages will be introduced in roadmap order: parsers, normalization, fingerprinting, indexing, retrieval, matching, and classification.

The package exposes package and algorithm version constants separately so a release cannot silently reinterpret persisted fingerprints.

M1 pins the tree-sitter runtime and each grammar distribution in both `pyproject.toml` and `requirements.lock`. Adapter versions carry the grammar distribution version; a grammar upgrade requires new golden results and an explicit lockfile change.
