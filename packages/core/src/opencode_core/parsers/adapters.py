"""Replaceable language adapter contracts and deterministic detection."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from opencode_core.parsers.model import TokenizationResult, UnsupportedLanguageError


class LanguageAdapter(Protocol):
    @property
    def language(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def extensions(self) -> frozenset[str]: ...

    def tokenize(self, source: bytes) -> TokenizationResult: ...


class AdapterRegistry:
    """Immutable-by-convention registry with explicit-over-extension detection."""

    def __init__(self, adapters: Iterable[LanguageAdapter]) -> None:
        ordered = tuple(sorted(adapters, key=lambda adapter: adapter.language))
        self._by_language = {adapter.language: adapter for adapter in ordered}
        by_extension: dict[str, LanguageAdapter] = {}
        for adapter in ordered:
            for extension in adapter.extensions:
                if extension in by_extension:
                    raise ValueError(f"ambiguous language extension: {extension}")
                by_extension[extension] = adapter
        self._by_extension = by_extension

    @property
    def languages(self) -> tuple[str, ...]:
        return tuple(self._by_language)

    def detect(
        self, path: str, explicit: str | None = None, prefix: bytes = b""
    ) -> LanguageAdapter:
        if explicit is not None:
            try:
                return self._by_language[explicit.casefold()]
            except KeyError as error:
                raise UnsupportedLanguageError(f"unsupported language: {explicit}") from error
        filename = path.casefold()
        matches = [
            adapter
            for extension, adapter in self._by_extension.items()
            if filename.endswith(extension)
        ]
        if len(matches) == 1:
            return matches[0]
        header = prefix[:256].decode("utf-8", errors="ignore").casefold()
        if header.startswith("#!"):
            if "python" in header:
                return self._by_language["python"]
            if "node" in header or "deno" in header:
                return self._by_language["javascript"]
        raise UnsupportedLanguageError(f"cannot determine language for: {path}")
