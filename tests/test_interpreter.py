import pytest
from src.interpret_results import interpret_hits

def test_interpret_hits_valid():
    hits = [{"gene": "geneA", "identity": 99.0, "length": 50}]
    results = interpret_hits(hits, "data/gene_class_map.csv")
    assert results[0]["class"] == "Beta-lactam"

def test_interpret_hits_unknown_gene():
    hits = [{"gene": "unknownGene", "identity": 99.0, "length": 50}]
    results = interpret_hits(hits, "data/gene_class_map.csv")
    assert results[0]["class"] == "Unknown"
