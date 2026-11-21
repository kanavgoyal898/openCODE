from __future__ import annotations

from pathlib import Path

from opencode_core.config import CoreSettings
from opencode_core.parsers import SourceScanner, default_registry


def test_scanner_is_bounded_and_never_follows_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "ok.py").write_text("value = 1\n", encoding="utf-8")
    (root / "ignored.txt").write_text("not source", encoding="utf-8")
    (root / "binary.js").write_bytes(b"x=\x00")
    (root / "large.java").write_text("class TooLarge {}", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n", encoding="utf-8")
    (root / "escape.py").symlink_to(outside)
    deep = root / "one" / "two"
    deep.mkdir(parents=True)
    (deep / "deep.py").write_text("deep = 1\n", encoding="utf-8")
    scanner = SourceScanner(
        default_registry(),
        CoreSettings(max_file_bytes=15, max_directory_depth=1, max_files=10),
    )

    files = list(scanner.scan(root))

    assert [(str(item.path), item.language) for item in files] == [("ok.py", "python")]
    assert {item.code for item in scanner.diagnostics} == {
        "BINARY_FILE",
        "DIRECTORY_TOO_DEEP",
        "FILE_TOO_LARGE",
        "SYMLINK_SKIPPED",
    }


def test_scanner_applies_stable_path_order_and_file_limit(tmp_path: Path) -> None:
    for name in ("c.py", "a.py", "b.py"):
        (tmp_path / name).write_text("x = 1\n", encoding="utf-8")
    scanner = SourceScanner(default_registry(), CoreSettings(max_files=2))

    files = list(scanner.scan(tmp_path))

    assert [str(item.path) for item in files] == ["a.py", "b.py"]
    assert scanner.diagnostics[-1].code == "FILE_LIMIT_REACHED"


def test_scanner_honors_exclusions_and_shebang_detection(tmp_path: Path) -> None:
    (tmp_path / "tool").write_text("#!/usr/bin/env python3\nvalue = 1\n", encoding="utf-8")
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "copy.py").write_text("value = 1\n", encoding="utf-8")
    scanner = SourceScanner(default_registry(), exclude_patterns=("generated",))

    files = list(scanner.scan(tmp_path))

    assert [(str(item.path), item.language) for item in files] == [("tool", "python")]
    assert [(str(item.path), item.code) for item in scanner.diagnostics] == [
        ("generated", "EXCLUDED")
    ]
