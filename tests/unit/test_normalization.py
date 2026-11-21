from __future__ import annotations

import unicodedata

import pytest
from opencode_core.normalization import Mode, normalize
from opencode_core.parsers import default_registry
from opencode_core.parsers.model import Token


def _tokens(source: str, path: str = "sample.py") -> tuple[Token, ...]:
    return default_registry().detect(path).tokenize(source.encode()).tokens


def _canonical(source: str, mode: Mode, path: str = "sample.py") -> tuple[str, ...]:
    return tuple(token.canonical for token in normalize(_tokens(source, path), mode))


def test_comments_and_layout_do_not_change_exact_stream() -> None:
    compact = "def add(left, right):\n return left + right\n"
    formatted = "def add( left , right ): # comment\n    return left + right\n"

    assert _canonical(compact, "exact") == _canonical(formatted, "exact")


def test_identifier_renaming_changes_exact_but_not_renamed_stream() -> None:
    first = "def add(left, right):\n return left + right\n"
    second = "def total(first, second):\n return first + second\n"

    assert _canonical(first, "exact") != _canonical(second, "exact")
    assert _canonical(first, "renamed") == _canonical(second, "renamed")


def test_member_and_local_identifiers_have_distinct_placeholders() -> None:
    stream = _canonical("def read(obj):\n return obj.value + value\n", "renamed")

    assert "ID_MEMBER_0" in stream
    assert "ID_LOCAL_0" in stream
    assert "ID_LOCAL_1" in stream


def test_placeholders_restart_in_nested_lexical_scopes() -> None:
    stream = _canonical(
        "def outer(value):\n def inner(value):\n  return value\n return value\n",
        "renamed",
    )

    assert stream.count("ID_LOCAL_0") >= 2


def test_literal_policy_separates_exact_and_renamed_modes() -> None:
    first = _tokens("value = 0x10\ntext = 'first'\n")
    equivalent_number = _tokens("value = 16\ntext = 'second'\n")

    first_exact = tuple(token.canonical for token in normalize(first, "exact"))
    second_exact = tuple(token.canonical for token in normalize(equivalent_number, "exact"))
    first_renamed = tuple(token.canonical for token in normalize(first, "renamed"))
    second_renamed = tuple(token.canonical for token in normalize(equivalent_number, "renamed"))

    assert "NUM_INT:16" in first_exact
    assert first_exact != second_exact
    assert first_renamed == second_renamed


def test_unicode_identifiers_are_nfc_normalized_and_keep_source_span() -> None:
    decomposed = "e\N{COMBINING ACUTE ACCENT}"
    normalized = normalize(_tokens(f"{decomposed} = 1\n"), "exact")
    identifier = next(token for token in normalized if token.kind == "identifier")

    assert identifier.canonical == unicodedata.normalize("NFC", decomposed)
    assert identifier.source.canonical == decomposed


def test_normalization_is_repeatable_and_rejects_unknown_mode() -> None:
    tokens = _tokens("value = 1\n")
    expected = normalize(tokens, "renamed")

    assert all(normalize(tokens, "renamed") == expected for _ in range(100))
    with pytest.raises(ValueError, match="unsupported normalization mode"):
        normalize(tokens, "semantic")  # type: ignore[arg-type]
