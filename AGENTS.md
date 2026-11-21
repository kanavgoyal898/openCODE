
## Spec-Driven Development Rules

These instructions are mandatory for every human or coding agent working in this repository. The repository is currently documentation-only; do not implement application code until the specification phase is explicitly approved.

1. The `specs/` directory is the authoritative source
   for formal implementation requirements and contracts.

2. The `docs/` directory contains supporting architecture,
   design decisions, explanations, and project plans.

3. Before implementing a feature, read its relevant
   specification files.

4. Every implementation change must be traceable to
   one or more documented requirements.

5. When an approved requirement changes, update the
   corresponding Markdown files in the same change.

6. Keep APIs, schemas, algorithms, and acceptance tests
   consistent with the specifications.

7. Record major architectural decisions under `docs/adr/`.

8. Never replace persisted specifications with
   chat-only descriptions.

9. Do not delete specification files without explicit
   authorization.

10. Before reporting a milestone complete, verify that
    the relevant specs exist, are current, and are
    consistent with the implementation.

11. Stable requirement definitions live only in `specs/requirements.md`; references may reuse IDs but must not redefine them.

12. Before code changes, read `specs/requirements.md`, the affected contract files, `specs/test-cases.md`, and the relevant roadmap milestone.

13. Preserve deterministic behavior, version all wire/data/algorithm contracts, and add a migration or ADR before breaking changes.

14. Never execute analyzed source, follow repository-controlled links outside the scan root, or log raw source and credentials.

15. Keep requirement → contract → test → acceptance mappings current in `specs/traceability-matrix.md`.

16. Run documentation validation after documentation changes: required-file presence/non-empty checks, relative-link checks, unique requirement-definition checks, and traceability checks.

17. Major decisions belong in `docs/adr/` using status, context, decision, consequences, and alternatives. Do not silently contradict an accepted ADR.

## Git and GitHub Workflow

1. Use the existing Git repository and configured GitHub remote. Fetch before integrating or publishing work; never overwrite remote changes.

2. At the end of each completed milestone, run its relevant tests and validation, stage only that milestone's files, create a descriptive Conventional Commit, and push it to the configured remote.

3. Use commit subjects such as `docs: add specification documents`, `feat: implement token normalization`, `feat: add Winnowing fingerprinting`, `test: add clone detection tests`, and `fix: correct fingerprint indexing`.

4. Never commit credentials, secrets, `.env` files, generated secret material, or credential-bearing repository URLs. Inspect staged content before committing.

5. Never force-push. If authentication or permissions prevent a push, report the exact failure and do not claim publication.

6. After every push, fetch or query the remote and verify that the destination branch resolves to the pushed commit.
