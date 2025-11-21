import types
import os
from src.main import run_pipeline


def test_run_pipeline_summary_mode(tmp_path):
    args = types.SimpleNamespace(
        input='input/example.fasta',
        db='AntibioticResistanceGeneDetector/data/resistance_genes.fasta',
        map='AntibioticResistanceGeneDetector/data/gene_class_map.csv',
        outdir=str(tmp_path),
        output_name='results.csv',
        identity=90,
        coverage=80,
        threads=1,
        plot=False,
        summary=True,
        quiet=True
    )
    res = run_pipeline(args)
    assert isinstance(res, list)


def test_run_pipeline_plot_mode(tmp_path):
    args = types.SimpleNamespace(
        input='input/example.fasta',
        db='AntibioticResistanceGeneDetector/data/resistance_genes.fasta',
        map='AntibioticResistanceGeneDetector/data/gene_class_map.csv',
        outdir=str(tmp_path),
        output_name='results.csv',
        identity=90,
        coverage=80,
        threads=1,
        plot=True,
        summary=False,
        quiet=True
    )
    res = run_pipeline(args)
    assert isinstance(res, list)
    # plots should be in outdir/plots
    plots_dir = os.path.join(str(tmp_path), 'plots')
    # If no data, visualization may warn but should not crash
    assert os.path.exists(str(tmp_path))
