# System Architecture

The system uses a ports-and-adapters core so the fingerprint engine runs in memory without web or database packages. Concrete CLI, HTTP, PostgreSQL, blob, parser, and queue adapters surround application services.

```mermaid
flowchart TB
  subgraph Edge
    CLI[CLI] API[REST API] WEB[Web UI]
  end
  CLI --> APP[Application services]
  API --> APP
  WEB --> API
  APP --> ENG[Standalone engine]
  APP --> IDX[FingerprintIndex port]
  APP --> JOB[JobQueue port]
  IDX --> PG[(PostgreSQL)]
  JOB --> WK[Workers]
  WK --> ENG
  WK --> PG
  WK --> BLOB[(Restricted source blobs)]
```

The engine owns adapters, normalization, rolling hash/Winnowing, retrieval policy, verification, classification, and aggregation interfaces. Application services own authorization, transactions, idempotency, scan lifecycle, and retention. Background workers isolate costly parsing; the API never parses large repositories inline. The [normative architecture](../specs/architecture.md), [data model](../specs/data-model.md), and [deployment](17-deployment-architecture.md) define boundaries and failure behavior.

Four independent plugins implement the common detector port: Exact and Token engines use positional fingerprint indexes; Structural uses AST fingerprints plus approximate retrieval and alignment; Semantic uses a separately versioned vector index and multi-evidence verifier. The aggregator preserves each engine's scores and evidence state while deduplicating canonical fragment pairs. See [detector contracts](../specs/detection-engines.md) and [ADR-006](adr/ADR-006-pluggable-clone-engines.md).
