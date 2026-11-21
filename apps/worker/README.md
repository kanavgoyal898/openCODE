# Worker application

The M8 worker executes durable PostgreSQL-backed scan jobs idempotently. The API records `queued` state before dispatch; `process_scan` transitions through running to completed/partial/failed and atomically persists revisions, fragments, postings, matches, and evidence. A process supervisor can recover queued jobs after restart.

Per ADR-001, no Redis/Celery dependency is introduced until queue-latency or concurrency evidence requires it.
