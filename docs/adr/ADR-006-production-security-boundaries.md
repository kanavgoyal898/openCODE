# ADR-006: Production Security Boundaries

## Status

Accepted for M11.

## Context

Repository bytes, source paths, API bodies, and clone evidence are attacker-controlled. The existing parser already avoided execution and rejected symlink traversal, but service defaults still allowed source evidence retrieval, containers shared an egress-capable network, and the API lacked centralized quotas, security headers, safe request telemetry, and an active-work cap.

## Decision

Defense ownership is split by boundary: ingestion owns per-file, total-byte, depth, and file-count limits; the API owns request-size and active-scan admission, authentication, source-display policy, response headers, and allowlisted structured telemetry; deployment owns read-only filesystems, non-root users, dropped capabilities, PID/scratch limits, and an internal backend network. Raw source access is disabled by default and must be explicitly enabled for a trusted local deployment. Production ingress must independently reject chunked or declared bodies over the same configured maximum.

The invariant is that untrusted source is parsed as bounded data without execution, does not leave the evidence boundary by default, and cannot grant the worker ambient host or Internet authority. A single-process timeout was rejected because it cannot preempt a native parser safely; production enforces job wall time by terminating the restricted worker container, while parser work remains bounded by file and corpus quotas.

## Consequences

Local operators who want side-by-side source must opt in with `OPENCODE_EXPOSE_SOURCE=true`. Horizontal API replicas require ingress or shared-store rate limiting in addition to the per-replica active-scan guard. The internal Compose network blocks Internet egress but is not a substitute for orchestrator network policy, seccomp/AppArmor, encrypted secrets, or managed database authorization. Parser and container runtime zero-days remain residual risks.

## Verification

`TC-SEC-*` and `TC-OBS-001` cover source suppression, request and repository quotas, traversal controls, headers, non-secret structured logs, and deployment configuration. The controls and residual risks remain synchronized with [the threat model](../14-security-threat-model.md) and [deployment architecture](../17-deployment-architecture.md).
