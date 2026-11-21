"""Versioned language adapters and safe source ingestion."""

from opencode_core.parsers.adapters import AdapterRegistry, LanguageAdapter
from opencode_core.parsers.ingestion import SourceScanner
from opencode_core.parsers.model import (
    Diagnostic,
    ParseCoverageError,
    SourceFile,
    Token,
    TokenizationResult,
    UnsupportedLanguageError,
)
from opencode_core.parsers.tree_sitter_adapter import default_registry

__all__ = [
    "AdapterRegistry",
    "Diagnostic",
    "LanguageAdapter",
    "ParseCoverageError",
    "SourceFile",
    "SourceScanner",
    "Token",
    "TokenizationResult",
    "UnsupportedLanguageError",
    "default_registry",
]
