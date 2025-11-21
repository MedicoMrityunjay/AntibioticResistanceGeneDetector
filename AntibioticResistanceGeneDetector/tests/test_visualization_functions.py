import os
import pandas as pd
from src import visualization


def test_visualization_empty(tmp_path, monkeypatch):
    # Ensure Agg backend for headless
    import matplotlib
    matplotlib.use('Agg')
    results = []
    visualization.plot_gene_heatmap(results, filename=str(tmp_path / 'heatmap.png'))
    visualization.plot_class_bar(results, filename=str(tmp_path / 'classbar.png'))
    visualization.plot_gene_class_network(results, filename=str(tmp_path / 'network.png'))
    # Files should not be created for empty data (module prints and returns)
    assert not (tmp_path / 'heatmap.png').exists()


def test_visualization_with_data(tmp_path):
    import matplotlib
    matplotlib.use('Agg')
    results = [
        {"sample_id": "s1", "gene": "geneA", "identity": 99.0, "length": 50, "antibiotic_class": "Beta-lactam", "source_file": "input/s1.fasta"},
        {"sample_id": "s2", "gene": "geneB", "identity": 98.0, "length": 45, "antibiotic_class": "Tetracycline", "source_file": "input/s2.fasta"}
    ]
    visualization.plot_gene_heatmap(results, filename=str(tmp_path / 'heatmap.png'))
    visualization.plot_class_bar(results, filename=str(tmp_path / 'classbar.png'))
    visualization.plot_gene_class_network(results, filename=str(tmp_path / 'network.png'))
    # Since the functions save to output/plots by default, check that files exist in that folder
    assert os.path.exists('output/plots/gene_heatmap.png') or os.path.exists(str(tmp_path / 'heatmap.png'))
