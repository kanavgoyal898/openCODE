from __future__ import annotations

import pytest
from opencode_core.parsers import ParseCoverageError, default_registry
from opencode_core.parsers.model import InvalidEncodingError


@pytest.mark.parametrize(
    ("path", "source", "language", "identifier"),
    [
        ("sample.py", b"def add(left, right):\n    return left + right\n", "python", "add"),
        ("sample.js", b"function add(left, right) { return left + right; }\n", "javascript", "add"),
        (
            "sample.ts",
            b"function add(left: number, right: number): number { return left + right; }\n",
            "typescript",
            "add",
        ),
        (
            "Sample.java",
            b"class Sample { int add(int left, int right) { return left + right; } }\n",
            "java",
            "add",
        ),
    ],
)
def test_supported_adapters_emit_ordered_tokens(
    path: str, source: bytes, language: str, identifier: str
) -> None:
    adapter = default_registry().detect(path)
    result = adapter.tokenize(source)

    assert result.language == language
    assert not result.degraded
    assert any(
        token.kind == "identifier" and token.canonical == identifier for token in result.tokens
    )
    assert list(result.tokens) == sorted(result.tokens, key=lambda token: token.start_byte)
    assert all(
        source[token.start_byte : token.end_byte].decode() == token.canonical
        for token in result.tokens
    )


def test_unicode_and_crlf_coordinates_use_original_bytes() -> None:
    source = "# comment\r\n𝛼 = 'value'\r\n".encode()  # noqa: RUF001
    result = default_registry().detect("unicode.py").tokenize(source)
    identifier = next(token for token in result.tokens if token.kind == "identifier")

    assert identifier.canonical == "𝛼"  # noqa: RUF001
    assert (identifier.start_byte, identifier.end_byte) == (11, 15)
    assert (identifier.start_line, identifier.start_column) == (2, 1)
    assert (identifier.end_line, identifier.end_column) == (2, 2)


def test_bom_is_removed_without_losing_original_byte_offsets() -> None:
    result = default_registry().detect("bom.py").tokenize(b"\xef\xbb\xbfvalue = 1\n")
    first = result.tokens[0]

    assert first.canonical == "value"
    assert first.start_byte == 3
    assert first.start_column == 1


def test_invalid_utf8_is_rejected() -> None:
    with pytest.raises(InvalidEncodingError, match="valid UTF-8"):
        default_registry().detect("invalid.py").tokenize(b"value = \xff")


def test_severely_malformed_source_is_rejected() -> None:
    with pytest.raises(ParseCoverageError, match=r"below 0\.900"):
        default_registry().detect("broken.py").tokenize(b"'" * 100)


def test_detection_prefers_explicit_language_and_rejects_unknown() -> None:
    registry = default_registry()

    assert registry.detect("no-extension", explicit="java").language == "java"
    with pytest.raises(ValueError, match="cannot determine"):
        registry.detect("README")
