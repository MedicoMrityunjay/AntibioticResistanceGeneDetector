import pytest
from src.gene_detector import detect_genes

def test_detect_genes_valid():
    hits = detect_genes("input/example.fasta", "data/resistance_genes.fasta")
    assert isinstance(hits, list)
    assert all("gene" in hit for hit in hits)

def test_detect_genes_missing_file():
    from src.error_handling import MissingFileError
    with pytest.raises(MissingFileError):
        detect_genes("input/missing.fasta", "data/resistance_genes.fasta")

def test_detect_genes_empty_fasta(tmp_path):
    from src.error_handling import CorruptedInputError
    empty_fasta = tmp_path / "empty.fasta"
    empty_fasta.write_text("")
    with pytest.raises(CorruptedInputError):
        detect_genes(str(empty_fasta), "data/resistance_genes.fasta")
