"""Bounded, non-following source tree enumeration for untrusted repositories."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from opencode_core.config import CoreSettings
from opencode_core.parsers.adapters import AdapterRegistry
from opencode_core.parsers.model import Diagnostic, SourceFile, UnsupportedLanguageError


class SourceScanner:
    def __init__(
        self,
        registry: AdapterRegistry,
        settings: CoreSettings | None = None,
        exclude_patterns: tuple[str, ...] = (),
    ) -> None:
        self.registry = registry
        self.settings = CoreSettings() if settings is None else settings
        self.exclude_patterns = exclude_patterns
        self.diagnostics: list[Diagnostic] = []

    def scan(self, root: Path) -> Iterator[SourceFile]:
        root = root.resolve(strict=True)
        if not root.is_dir():
            raise NotADirectoryError(root)
        self.diagnostics.clear()
        accepted = 0
        for current, directories, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            depth = len(current_path.relative_to(root).parts)
            directories[:] = sorted(
                directory
                for directory in directories
                if self._allow_directory(root, current_path / directory, depth + 1)
            )
            for filename in sorted(files):
                path = current_path / filename
                relative = PurePosixPath(path.relative_to(root).as_posix())
                if self._excluded(relative):
                    self._diagnose(relative, "EXCLUDED", "path matches an exclusion pattern")
                    continue
                if path.is_symlink():
                    self._diagnose(relative, "SYMLINK_SKIPPED", "symbolic links are not scanned")
                    continue
                try:
                    with path.open("rb") as stream:
                        prefix = stream.read(256)
                    adapter = self.registry.detect(filename, prefix=prefix)
                except UnsupportedLanguageError:
                    continue
                stat = path.stat(follow_symlinks=False)
                if stat.st_size > self.settings.max_file_bytes:
                    self._diagnose(relative, "FILE_TOO_LARGE", "file exceeds configured byte limit")
                    continue
                if accepted >= self.settings.max_files:
                    self._diagnose(relative, "FILE_LIMIT_REACHED", "repository file limit reached")
                    return
                content = path.read_bytes()
                if b"\x00" in content[:8192]:
                    self._diagnose(relative, "BINARY_FILE", "binary file was skipped")
                    continue
                accepted += 1
                yield SourceFile(str(root), relative, adapter.language, content)

    def _allow_directory(self, root: Path, path: Path, depth: int) -> bool:
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if self._excluded(relative):
            self._diagnose(relative, "EXCLUDED", "path matches an exclusion pattern")
            return False
        if path.is_symlink():
            self._diagnose(relative, "SYMLINK_SKIPPED", "symbolic links are not scanned")
            return False
        if depth > self.settings.max_directory_depth:
            self._diagnose(relative, "DIRECTORY_TOO_DEEP", "directory depth limit reached")
            return False
        return True

    def _excluded(self, path: PurePosixPath) -> bool:
        return any(path.match(pattern) for pattern in self.exclude_patterns)

    def _diagnose(self, path: PurePosixPath, code: str, message: str) -> None:
        self.diagnostics.append(Diagnostic(path, code, message))
