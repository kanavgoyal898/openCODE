"""Fingerprint index ports and the standalone in-memory adapter."""

from opencode_core.indexing.memory import InMemoryFingerprintIndex
from opencode_core.indexing.model import (
    FingerprintKey,
    FingerprintQuery,
    FragmentFingerprintSet,
    Posting,
    RevisionFingerprintSet,
)

__all__ = [
    "FingerprintKey",
    "FingerprintQuery",
    "FragmentFingerprintSet",
    "InMemoryFingerprintIndex",
    "Posting",
    "RevisionFingerprintSet",
]
