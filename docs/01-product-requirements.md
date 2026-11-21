# Product Requirements

## Users and jobs

| User | Job | Required outcome |
|---|---|---|
| Maintainer | find copy/paste and renamed duplication | ranked groups with exact ranges and evidence |
| Researcher | evaluate clone methods | versioned, reproducible reports and raw metrics |
| CI/tool author | automate checks | stable JSON/SARIF, exit codes, REST contracts |
| Reviewer | inspect a match | side-by-side tokens/source and limitations |

The MVP journeys are directory scan, repository ingestion, clone discovery, two-file comparison, snippet search, statistics, and reproducible benchmark. A no-match result is valid. Unsupported/degraded files are visible. Deletion and retention are user-controlled.

The normative requirements, milestone, verification method, and tests are in [requirements.md](../specs/requirements.md). Product release gates are in [acceptance-criteria.md](../specs/acceptance-criteria.md). The complete project supports all four recognized categories, but Type 4 results distinguish speculative retrieval candidates from multi-evidence verified matches. Out of scope: legal/plagiarism judgments, authorship attribution, universal program-equivalence proofs, and automatic license conclusions.
