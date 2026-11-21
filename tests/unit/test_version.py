from opencode_core.version import (
    FINGERPRINT_VERSION,
    NORMALIZATION_VERSION,
    PACKAGE_VERSION,
    REPORT_SCHEMA_VERSION,
)


def test_contract_versions_match_approved_specs() -> None:
    assert PACKAGE_VERSION == "0.1.0.dev0"
    assert NORMALIZATION_VERSION == "norm-v1"
    assert FINGERPRINT_VERSION == "fp-v1"
    assert REPORT_SCHEMA_VERSION == "1"
