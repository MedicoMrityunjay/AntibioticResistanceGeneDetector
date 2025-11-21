import pytest
from src.interpret_results import interpret_hits

def test_report_formatting():
    hits = [
        {"gene": "geneA", "identity": 99.0, "length": 50, "sample_id": "sample1"},
        {"gene": "geneB", "identity": 98.0, "length": 45, "sample_id": "sample2"}
    ]
    results = interpret_hits(hits, "AntibioticResistanceGeneDetector/data/gene_class_map.csv")
    for r in results:
        assert "sample_id" in r
        assert "gene" in r
        assert "identity" in r
        assert "coverage" in r
        assert "antibiotic_class" in r
