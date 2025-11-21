import pytest
import os
from src.gene_detector import detect_genes
from src.utils import validate_fasta
from src.error_handling import MissingFileError, CorruptedInputError

def test_empty_fasta(tmp_path):
    empty = tmp_path / "empty.fasta"
    empty.write_text("")
    with pytest.raises(CorruptedInputError):
        validate_fasta(str(empty))

def test_corrupted_fasta(tmp_path):
    bad = tmp_path / "bad.fasta"
    bad.write_text(">bad\nINVALIDSEQ\n>bad2\n")
    # BioPython may still parse but sequences lacking valid letters will parse; ensure validation catches emptiness
    with pytest.raises(CorruptedInputError):
        validate_fasta(str(bad))

def test_missing_db(tmp_path):
    sample = tmp_path / "sample.fasta"
    sample.write_text(">s\nATGCGTACG\n")
    # missing db should cause detect_genes to safe-fail and return []
    hits = detect_genes(str(sample), "nonexistent_db.fasta")
    assert hits == []
