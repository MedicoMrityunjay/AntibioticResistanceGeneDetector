import pytest
from src.run_blast import is_tool_installed

def test_blast_detection():
    # Should be False unless BLAST/DIAMOND is installed
    assert isinstance(is_tool_installed("blastn"), bool)
    assert isinstance(is_tool_installed("diamond"), bool)
