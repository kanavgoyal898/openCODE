"""Idempotent scan worker entry points."""

from opencode_worker.tasks import process_scan

__all__ = ["process_scan"]
