"""Order-preserving reversible unsigned-64 to signed-BIGINT mapping."""

SIGN = 1 << 63
MODULUS = 1 << 64


def u64_to_i64(value: int) -> int:
    if not 0 <= value < MODULUS:
        raise ValueError("value must be an unsigned 64-bit integer")
    mapped = value ^ SIGN
    return mapped - MODULUS if mapped >= SIGN else mapped


def i64_to_u64(value: int) -> int:
    if not -(1 << 63) <= value < SIGN:
        raise ValueError("value must be a signed 64-bit integer")
    mapped = value + MODULUS if value < 0 else value
    return mapped ^ SIGN
