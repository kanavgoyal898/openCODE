# REST API Contracts

Base path `/api/v1`; JSON is UTF-8. Authentication is bearer/OIDC in hosted mode. Every response carries `X-Request-Id`. Mutating POSTs accept `Idempotency-Key` (1–128 visible ASCII characters). IDs are UUID strings.

| Method/path | Request | Success | Principal errors |
|---|---|---|---|
| `POST /repositories` | `RepositoryCreate` | `201 Repository` | 400, 401, 409, 422 |
| `GET /repositories` | cursor, limit 1..100 | `200 Page<Repository>` | 400, 401 |
| `GET /repositories/{id}` | — | `200 Repository` | 401, 404 |
| `DELETE /repositories/{id}` | — | `202 Deletion` | 401, 404, 409 |
| `POST /scans` | `ScanCreate` | `202 Scan` | 400, 404, 409, 422, 429 |
| `GET /scans/{id}` | — | `200 Scan` | 401, 404 |
| `GET /clones` | repository, scan, type, cursor, limit | `200 Page<CloneSummary>` | 400, 401 |
| `GET /clones/{id}` | — | `200 CloneDetail` | 401, 404 |
| `POST /search` | `SearchRequest` | `200 SearchResult` | 400, 413, 422, 429 |
| `POST /compare` | `CompareRequest` | `200 CompareResult` | 400, 413, 422, 429 |
| `GET /health` | — | `200 Health` (liveness); `503` if not ready with `?ready=true` | 503 |

```typescript
type RepositoryCreate = {name: string; localPath?: string; remote?: {url: string; credentialRef?: string}; revision?: string};
type ScanCreate = {repositoryId: string; modes?: ("exact"|"renamed"|"structural"|"semantic"|"semantic-verified")[]; strict?: boolean};
type Scan = {id: string; repositoryId: string; status: "queued"|"running"|"completed"|"partial"|"failed"|"cancelled";
  algorithmVersion: "fp-v1"; normalizationVersion: "norm-v1"; counts: Record<string,number>; createdAt: string; completedAt?: string};
type SearchRequest = {repositoryIds: string[]; code: string; language: "python"|"javascript"|"typescript"|"java";
  mode?: "exact"|"renamed"; limit?: number};
type CompareRequest = {leftCode: string; rightCode: string; language: "python"|"javascript"|"typescript"|"java";
  mode?: "exact"|"renamed"};
type CompareResult = {items: CloneResult[]};
type SourceRange = {repositoryId:string; fileRevisionId:string; path:string;
  startByte:number; endByte:number; startLine:number; startColumn:number; endLine:number; endColumn:number};
type Evidence = {kind: "fingerprint"|"token"|"ast"|"embedding"|"control_flow"|"data_flow"|"pdg"|"behavioral";
  version: string; scores: Record<string,number|null>; explanationCodes: string[]; limitations: string[]};
type CloneResult = {category: "type1"|"type2"|"type3"|"type4";
  evidenceState: "verified"|"candidate"|"rejected"; detectorId: string; algorithmVersion: string;
  threshold: Record<string,number>; left: SourceRange; right: SourceRange; evidence: Evidence[];
  confidence: null|{value:number; calibrationDataset:string; calibrationVersion:string}};
type ApiError = {error: {code: string; message: string; requestId: string; details?: Record<string,unknown>}};
type Page<T> = {items: T[]; nextCursor: string|null};
```

Local paths are permitted only for the trusted single-user deployment and must be server-allowlisted. Remote credentials are references, never returned. Cursors are opaque, signed, and bind filters/order. Default order is creation time then ID. Unknown fields are rejected on writes. OpenAPI 3.1 generated from these schemas must pass lint and contract tests.

`POST /compare` treats both snippets as ephemeral input, never persists them, and returns deterministic verified Type 1/2 evidence only. `mode="exact"` returns Type 1 matches; `mode="renamed"` returns Type 2 matches. An empty `items` array is a successful no-match result.

Type 4 embedding-only results must use `evidenceState="candidate"`. APIs must not expose a verified semantic result unless its evidence satisfies the approved multi-evidence policy in [detection-engines.md](detection-engines.md).

`semantic` selects candidate-only `semantic-v1`. `semantic-verified` explicitly enables the `semantic-v2` static promotion policy; it does not enable behavioral execution. Unsupported constructs remain candidate-only in either mode.
