import pytest
import os
from src.gene_detector import batch_detect_genes

def test_batch_processing():
    results = batch_detect_genes("input", "AntibioticResistanceGeneDetector/data/resistance_genes.fasta")
    assert isinstance(results, dict)
    for sample_id, hits in results.items():
        assert isinstance(hits, list)
        for hit in hits:
            assert "gene" in hit
            assert "sample_id" in hit
