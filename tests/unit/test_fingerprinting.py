from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

import pytest
from opencode_core.fingerprinting import (
    BASE,
    Fingerprint,
    IncompatibleFingerprintVersionError,
    fingerprint,
    rolling_hashes,
    token_code,
    winnow,
)
from opencode_core.normalization import NormalizedToken, normalize
from opencode_core.parsers import default_registry

MASK = (1 << 64) - 1


def _normalized(source: str) -> tuple[NormalizedToken, ...]:
    tokens = default_registry().detect("sample.py").tokenize(source.encode()).tokens
    return normalize(tokens, "exact")


def _naive(codes: tuple[int, ...], size: int) -> tuple[int, ...]:
    values = []
    for start in range(len(codes) - size + 1):
        value = 0
        for code in codes[start : start + size]:
            value = ((value * BASE) + code) & MASK
        values.append(value)
    return tuple(values)


def test_token_code_and_hex_serialization_have_fixed_vectors() -> None:
    token = _normalized("value = 1\n")[0]

    assert token.canonical == "value"
    assert token_code(token) == 8_307_812_066_010_474_377
    assert Fingerprint(token_code(token), 0).hex == "734b470eaf422789"


def test_rolling_hash_matches_naive_recomputation() -> None:
    codes = tuple(range(1, 80))

    assert rolling_hashes(codes) == _naive(codes, 25)
    assert rolling_hashes(codes, 7) == _naive(codes, 7)


def test_winnowing_uses_rightmost_minimum_and_deduplicates_positions() -> None:
    assert winnow((9, 1, 1, 8, 7, 6), window_size=4) == (Fingerprint(1, 2),)
    assert winnow((1, 1, 9, 9, 9), window_size=3) == (
        Fingerprint(1, 1),
        Fingerprint(9, 4),
    )


def test_empty_short_and_threshold_streams_follow_contract() -> None:
    empty = fingerprint((), "exact")
    short = fingerprint(_normalized("value = 1\n"), "exact")
    exactly_k_codes = tuple(range(25))
    threshold_codes = tuple(range(28))

    assert empty.fingerprints == ()
    assert len(short.fingerprints) == 1 and short.fingerprints[0].small
    assert winnow(rolling_hashes(exactly_k_codes)) == ()
    assert len(winnow(rolling_hashes(threshold_codes))) == 1


def test_small_fingerprint_is_namespace_separated_and_deterministic() -> None:
    tokens = _normalized("value = 1\n")

    first = fingerprint(tokens, "exact")
    second = fingerprint(tokens, "exact")

    assert first == second
    assert first.fingerprints[0].hex == "535cc264b46a8e96"


def test_incompatible_versions_and_modes_are_rejected() -> None:
    exact = fingerprint(_normalized("value = 1\n"), "exact")

    exact.require_compatible(exact)
    with pytest.raises(IncompatibleFingerprintVersionError, match="incompatible"):
        exact.require_compatible(replace(exact, algorithm_version="fp-v2"))
    with pytest.raises(IncompatibleFingerprintVersionError, match="incompatible"):
        exact.require_compatible(replace(exact, mode="renamed"))


def test_fingerprint_output_is_stable_across_processes() -> None:
    script = """
import json
from opencode_core.fingerprinting import fingerprint
from opencode_core.normalization import normalize
from opencode_core.parsers import default_registry
tokens = default_registry().detect('x.py').tokenize(b'value = 1\\n').tokens
result = fingerprint(normalize(tokens, 'exact'), 'exact')
print(json.dumps([item.hex for item in result.fingerprints]))
"""
    outputs = [
        subprocess.check_output([sys.executable, "-c", script], text=True).strip() for _ in range(3)
    ]

    assert len(set(outputs)) == 1
    assert json.loads(outputs[0]) == ["535cc264b46a8e96"]


@pytest.mark.parametrize(("size", "window"), [(0, 4), (4, 0)])
def test_invalid_algorithm_parameters_are_rejected(size: int, window: int) -> None:
    if size == 0:
        with pytest.raises(ValueError, match="k-gram size"):
            rolling_hashes((1, 2, 3), size)
    else:
        with pytest.raises(ValueError, match="window size"):
            winnow((1, 2, 3, 4), window)
