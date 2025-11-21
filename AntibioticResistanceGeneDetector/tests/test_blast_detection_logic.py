import pytest
from src.run_blast import detect_search_tool, is_tool_installed


def test_detect_search_tool_returns_none_or_string():
    val = detect_search_tool()
    assert (val is None) or isinstance(val, str)


def test_is_tool_installed_type():
    assert isinstance(is_tool_installed('blastn'), bool)
    assert isinstance(is_tool_installed('diamond'), bool)
