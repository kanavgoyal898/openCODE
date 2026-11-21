"""The fp-v1 algorithm from specs/algorithm-contracts.md."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from opencode_core.normalization import Mode, NormalizedToken
from opencode_core.version import FINGERPRINT_VERSION, NORMALIZATION_VERSION

K_GRAM_SIZE = 25
WINDOW_SIZE = 4
BASE = 1_000_003
_MASK = (1 << 64) - 1


class IncompatibleFingerprintVersionError(ValueError):
    """Raised before comparing differently versioned fingerprint sets."""


@dataclass(frozen=True, order=True, slots=True)
class Fingerprint:
    hash_u64: int
    token_position: int
    small: bool = False

    @property
    def hex(self) -> str:
        return self.hash_u64.to_bytes(8, "big").hex()


@dataclass(frozen=True, slots=True)
class FingerprintSet:
    mode: Mode
    fingerprints: tuple[Fingerprint, ...]
    token_count: int
    algorithm_version: str = FINGERPRINT_VERSION
    normalization_version: str = NORMALIZATION_VERSION

    def require_compatible(self, other: FingerprintSet) -> None:
        own = (self.algorithm_version, self.normalization_version, self.mode)
        candidate = (other.algorithm_version, other.normalization_version, other.mode)
        if own != candidate:
            raise IncompatibleFingerprintVersionError(
                f"incompatible fingerprint sets: {own!r} != {candidate!r}"
            )


def token_code(token: NormalizedToken) -> int:
    encoded = f"{token.kind}\0{token.canonical}".encode()
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")


def rolling_hashes(codes: tuple[int, ...], size: int = K_GRAM_SIZE) -> tuple[int, ...]:
    if size <= 0:
        raise ValueError("k-gram size must be positive")
    if len(codes) < size:
        return ()
    current = 0
    for code in codes[:size]:
        current = ((current * BASE) + code) & _MASK
    hashes = [current]
    high_power = pow(BASE, size - 1, 1 << 64)
    for index in range(1, len(codes) - size + 1):
        outgoing = codes[index - 1]
        incoming = codes[index + size - 1]
        current = (current - (outgoing * high_power)) & _MASK
        current = ((current * BASE) + incoming) & _MASK
        hashes.append(current)
    return tuple(hashes)


def winnow(hashes: tuple[int, ...], window_size: int = WINDOW_SIZE) -> tuple[Fingerprint, ...]:
    if window_size <= 0:
        raise ValueError("window size must be positive")
    if len(hashes) < window_size:
        return ()
    selected: list[Fingerprint] = []
    last_position = -1
    for start in range(len(hashes) - window_size + 1):
        window = hashes[start : start + window_size]
        minimum = min(window)
        relative = max(index for index, value in enumerate(window) if value == minimum)
        position = start + relative
        if position != last_position:
            selected.append(Fingerprint(hashes[position], position))
            last_position = position
    return tuple(selected)


def _small_fingerprint(codes: tuple[int, ...]) -> Fingerprint:
    serialized = b"SMALL\0" + b"".join(code.to_bytes(8, "big") for code in codes)
    value = int.from_bytes(hashlib.sha256(serialized).digest()[:8], "big")
    return Fingerprint(value, 0, small=True)


def fingerprint(tokens: tuple[NormalizedToken, ...], mode: Mode) -> FingerprintSet:
    codes = tuple(token_code(token) for token in tokens)
    if not codes:
        selected: tuple[Fingerprint, ...] = ()
    elif len(codes) < K_GRAM_SIZE:
        selected = (_small_fingerprint(codes),)
    else:
        selected = winnow(rolling_hashes(codes))
    return FingerprintSet(mode=mode, fingerprints=selected, token_count=len(tokens))
