import pytest
from src.utils import validate_fasta, read_gene_class_map

def test_validate_fasta_valid():
    assert validate_fasta("input/example.fasta") is True

def test_read_gene_class_map():
    mapping = read_gene_class_map("data/gene_class_map.csv")
    assert mapping["geneA"] == "Beta-lactam"
    assert mapping["geneB"] == "Tetracycline"
