from scripts.validate_docs import REQUIRED, validate


def test_required_documentation_is_valid() -> None:
    assert len(REQUIRED) == 41
    assert validate() == []
