# Product Requirements

## Users and jobs

| User | Job | Required outcome |
|---|---|---|
| Maintainer | find copy/paste and renamed duplication | ranked groups with exact ranges and evidence |
| Researcher | evaluate clone methods | versioned, reproducible reports and raw metrics |
| CI/tool author | automate checks | stable JSON/SARIF, exit codes, REST contracts |
| Reviewer | inspect a match | side-by-side tokens/source and limitations |

The MVP journeys are directory scan, repository ingestion, clone discovery, two-file comparison, snippet search, statistics, and reproducible benchmark. A no-match result is valid. Unsupported/degraded files are visible. Deletion and retention are user-controlled.

The normative requirements, milestone, verification method, and tests are in [requirements.md](../specs/requirements.md). Product release gates are in [acceptance-criteria.md](../specs/acceptance-criteria.md). Out of scope: executing builds, legal/plagiarism judgments, authorship attribution, semantic equivalence, and automatic license conclusions.
