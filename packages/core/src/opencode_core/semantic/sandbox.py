"""Explicitly authorized runner for approved behavioral harnesses."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SandboxResult:
    status: str
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass(frozen=True, slots=True)
class BehavioralSandbox:
    enabled: bool = False
    network_isolated: bool = False
    timeout_seconds: float = 1.0
    output_bytes: int = 16_384
    memory_bytes: int = 128 * 1024 * 1024
    cpu_seconds: int = 1

    def run_approved_harness(self, harness: str) -> SandboxResult:
        if not self.enabled:
            return SandboxResult("disabled", None, "", "")
        if not self.network_isolated:
            return SandboxResult("isolation_required", None, "", "")

        def limits() -> None:
            if os.name != "posix":
                return
            import resource

            requested = (
                (resource.RLIMIT_CPU, self.cpu_seconds),
                (resource.RLIMIT_AS, self.memory_bytes),
                (resource.RLIMIT_FSIZE, self.output_bytes),
                (resource.RLIMIT_NOFILE, 16),
                (resource.RLIMIT_NPROC, 1),
            )
            for limit, value in requested:
                try:
                    _soft, hard = resource.getrlimit(limit)
                    bounded = value if hard < 0 else min(value, hard)
                    resource.setrlimit(limit, (bounded, hard))
                except (OSError, ValueError):
                    continue

        with tempfile.TemporaryDirectory(prefix="opencode-behavior-") as directory:
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", "-S", "-c", harness],
                    cwd=directory,
                    env={"PATH": ""},
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                    preexec_fn=limits if os.name == "posix" else None,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult("timeout", None, "", "")
        stdout = completed.stdout[: self.output_bytes].decode(errors="replace")
        stderr = completed.stderr[: self.output_bytes].decode(errors="replace")
        return SandboxResult("completed", completed.returncode, stdout, stderr)
