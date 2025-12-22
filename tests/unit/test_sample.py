"""Sample unit tests for CI/CD pipeline validation."""

import pytest


def test_example_pass():
    """This test should pass."""
    assert True


def test_example_calculation():
    """Test basic calculation."""
    assert 2 + 2 == 4


def test_string_operations():
    """Test string operations."""
    text = "FirefighterAI"
    assert text.upper() == "FIREFIGHTERAI"
    assert len(text) == 13


@pytest.mark.skip(reason="Example of skipped test")
def test_example_skip():
    """This test is skipped."""
    assert False