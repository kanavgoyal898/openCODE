from __future__ import annotations

import pytest
from opencode_core.config import ConfigurationError, CoreSettings


def test_settings_use_safe_defaults() -> None:
    assert CoreSettings.from_environment({}) == CoreSettings()


def test_settings_accept_positive_resource_limits() -> None:
    settings = CoreSettings.from_environment(
        {
            "OPENCODE_MAX_FILE_BYTES": "4096",
            "OPENCODE_MAX_DIRECTORY_DEPTH": "8",
            "OPENCODE_MAX_FILES": "250",
        }
    )

    assert settings == CoreSettings(
        max_file_bytes=4096,
        max_directory_depth=8,
        max_files=250,
    )


@pytest.mark.parametrize("raw", ["0", "-1", "invalid"])
def test_settings_reject_invalid_limits(raw: str) -> None:
    with pytest.raises(ConfigurationError):
        CoreSettings.from_environment({"OPENCODE_MAX_FILE_BYTES": raw})
