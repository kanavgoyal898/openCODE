"""The exact and renamed normalization modes defined by norm-v1."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from opencode_core.parsers.model import Token
from opencode_core.version import NORMALIZATION_VERSION

Mode = Literal["exact", "renamed"]
_INTEGER_SUFFIX = re.compile(r"[lL]$")
_FLOAT_SUFFIX = re.compile(r"[fFdD]$")


@dataclass(frozen=True, slots=True)
class NormalizedToken:
    kind: str
    canonical: str
    source: Token


def _literal_category(token: Token) -> str:
    subtype = (token.subtype or "").casefold()
    text = token.canonical.casefold()
    if token.kind == "string":
        if "template" in subtype:
            return "TEMPLATE"
        if "character" in subtype:
            return "CHAR"
        return "STRING"
    if any(marker in subtype for marker in ("float", "decimal")) or any(
        marker in text for marker in (".", "e", "p")
    ):
        return "FLOAT"
    return "INT"


def _canonical_number(text: str) -> str:
    compact = text.replace("_", "")
    integer = _INTEGER_SUFFIX.sub("", compact)
    try:
        return str(int(integer, 0))
    except ValueError:
        floating = _FLOAT_SUFFIX.sub("", compact)
        try:
            value = Decimal(floating)
        except InvalidOperation:
            return unicodedata.normalize("NFC", compact)
        if not value.is_finite():
            return unicodedata.normalize("NFC", compact)
        normalized = format(value.normalize(), "f")
        return "0" if normalized in {"-0", "-0.0"} else normalized


def _exact_literal(token: Token) -> str:
    category = _literal_category(token)
    if token.kind == "number":
        return f"NUM_{category}:{_canonical_number(token.canonical)}"
    digest = hashlib.sha256(token.canonical.encode("utf-8")).hexdigest()[:16]
    return f"STR_{category}:{digest}"


def normalize(tokens: tuple[Token, ...], mode: Mode) -> tuple[NormalizedToken, ...]:
    """Normalize an ordered token stream while retaining source coordinates."""

    if mode not in ("exact", "renamed"):
        raise ValueError(f"unsupported normalization mode: {mode}")
    identifiers: dict[tuple[str, str, str], str] = {}
    counters: dict[tuple[str, str], int] = {}
    normalized: list[NormalizedToken] = []
    for token in tokens:
        canonical = unicodedata.normalize("NFC", token.canonical)
        if token.kind == "identifier":
            if mode == "renamed":
                role = (token.role or "local").upper()
                key = (token.scope_id, role, canonical)
                counter_key = (token.scope_id, role)
                if key not in identifiers:
                    index = counters.get(counter_key, 0)
                    identifiers[key] = f"ID_{role}_{index}"
                    counters[counter_key] = index + 1
                canonical = identifiers[key]
        elif token.kind in {"string", "number"}:
            canonical = (
                f"STR_{_literal_category(token)}"
                if mode == "renamed" and token.kind == "string"
                else f"NUM_{_literal_category(token)}"
                if mode == "renamed"
                else _exact_literal(token)
            )
        normalized.append(NormalizedToken(token.kind, canonical, token))
    return tuple(normalized)


__all__ = ["NORMALIZATION_VERSION", "Mode", "NormalizedToken", "normalize"]
