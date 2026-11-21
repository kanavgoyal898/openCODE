# ADR-001: Technology Stack

- Status: Accepted
- Date: 2026-11-22

## Context

openCODE needs safe native-speed parsing, deterministic core behavior, a productive API/CLI, PostgreSQL bulk indexing, background work, and an accessible web UI. The core must remain usable without the web or database.

## Decision

Use Python 3.13 for the initial application/core with strict typing, tree-sitter language bindings pinned by checksum, PostgreSQL 17 for hosted persistence, a PostgreSQL-backed durable job abstraction initially, FastAPI-compatible OpenAPI 3.1 HTTP patterns, and a TypeScript/React web client. Package the CLI and services from shared application/core modules; deploy OCI images on Linux.

Concrete library choices remain replaceable adapters and must be lockfile-pinned. Rust acceleration may be introduced behind the same fingerprint port only after profiling and golden-vector equivalence.

## Consequences

Python accelerates delivery and parser integration but makes profiling/resource isolation important. PostgreSQL provides transactions and posting indexes but requires bulk-load discipline. Two UI/runtime languages add build complexity. Algorithm serialization—not host integer behavior—defines determinism.

## Alternatives

All-Rust offered stronger resource control but slower initial service development; JVM simplified Java tooling but increased footprint; Elasticsearch added operational cost before scale evidence. Reconsider only through a superseding ADR and unchanged contracts.
