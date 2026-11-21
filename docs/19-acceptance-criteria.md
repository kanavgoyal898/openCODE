# Acceptance Criteria Guide

Acceptance is evidence-based: each requirement has a stable ID, milestone, verification method, and test mapping in [formal requirements](../specs/requirements.md). Normative release gates are [specs/acceptance-criteria.md](../specs/acceptance-criteria.md); this guide explains review.

Reviewers confirm deterministic fixtures, parser/version manifests, atomic data behavior, source-range evidence, conservative clone classification, API/CLI schema compatibility, security limits, deletion/retention, accessibility, and benchmark provenance. Quantitative performance and accuracy statements must show measured dataset/hardware/version and remain distinct from targets.

A failed mandatory test, stale posting, unbounded hostile input, source/secret leak, inaccessible critical flow, or mismatch among requirement/contract/test is release-blocking. Preview exceptions may cover only missed performance targets, must be explicit, and may not waive correctness or security. Type 3 is accepted only with structural/alignment evidence; Type 4 embedding results remain speculative candidates unless the approved multi-evidence policy verifies them. Plagiarism and universal-equivalence conclusions are never accepted behavior.
