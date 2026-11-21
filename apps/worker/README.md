# Worker application

The M8 worker will execute idempotent scan application services with explicit resource boundaries. Per ADR-001 and the deployment specification, no Redis/Celery dependency is introduced until the asynchronous design demonstrates that it is required.
