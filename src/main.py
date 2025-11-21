"""
Main entry point for Antibiotic Resistance Gene Detector.

This module contains the CLI entrypoint that parses arguments and
orchestrates the detection pipeline: validation, detection, interpretation,
reporting and optional plotting.
"""

import os
import logging
import argparse
from src.gene_detector import detect_genes, batch_detect_genes
from src.interpret_results import interpret_hits, write_report
from src.utils import setup_logging
from src.rich_utils import get_console, get_progress, setup_rich_logging


def run_pipeline(args, progress=None):
    """
    Execute the detection pipeline using a parsed arguments namespace.

    Parameters
    ----------
    args : argparse.Namespace or similar
        Object providing CLI-like attributes used by the pipeline (e.g.
        ``input``, ``db``, ``map``, ``outdir``, ``identity``, ``coverage``).
    progress : callable, optional
        Optional callback that receives stage messages: progress(str).

    Returns
    -------
    list of dict
        Combined interpreted results produced by the run (may be empty).
    """
    def _p(msg: str):
        try:
            if progress:
                progress(msg)
        except Exception:
            pass
    # Setup logging and optionally Rich. Support callers that don't have `rich` attribute.
    rich_flag = getattr(args, 'rich', True)
    quiet_flag = getattr(args, 'quiet', False)
    setup_rich_logging(rich_enabled=rich_flag, quiet=quiet_flag)
    setup_logging(quiet=quiet_flag if hasattr(args, 'quiet') else False, log_dir=os.path.join(args.outdir, 'logs') if hasattr(args, 'outdir') else 'output/logs')
    console = get_console(rich_enabled=rich_flag, quiet=quiet_flag)
    progress_ctor = get_progress(rich_enabled=rich_flag, console=console)

    _p("Loading input sequences")

    # Validate input
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input path not found: {args.input}")

    # Ensure outdir exists and writable
    _p("Preparing database")
    outdir = args.outdir if hasattr(args, 'outdir') and args.outdir else 'output'
    os.makedirs(outdir, exist_ok=True)
    testfile = os.path.join(outdir, '.write_test')
    try:
        with open(testfile, 'w') as f:
            f.write('ok')
        os.remove(testfile)
    except Exception as e:
        raise PermissionError(f"Cannot write to output directory {outdir}: {e}")

    is_dir = os.path.isdir(args.input)

    if is_dir:
        # Batch mode
        _p("Running BLAST search")
        batch_results = batch_detect_genes(args.input, args.db, args.identity, args.coverage, threads=args.threads, output_dir=outdir, write_per_sample=not args.summary, console=console, rich_enabled=rich_flag)
        all_results = []
        for sample_id, hits in batch_results.items():
            _p("Filtering hits")
            results = interpret_hits(hits, args.map)
            out_path = os.path.join(outdir, f"{sample_id}_results.csv")
            # Save per-sample unless summary mode
            write_report(results, out_path, save=not args.summary, console=console, rich_enabled=rich_flag)
            all_results.extend(results)
        # Combined report
        _p("Building summary")
        write_report(all_results, os.path.join(outdir, args.output_name), save=not args.summary, console=console, rich_enabled=rich_flag)
        combined_results = all_results
    else:
        # Single-file mode
        # Validate FASTA readability
        from src.utils import validate_fasta
        try:
            # use console status if available
            if console is not None and rich_flag:
                with console.status(f"Validating {args.input}..."):
                    validate_fasta(args.input)
            else:
                validate_fasta(args.input)
        except Exception as e:
            logging.error(f"Input FASTA invalid: {e}")
            if args.summary:
                console.print("Input FASTA invalid.") if console is not None else print("Input FASTA invalid.")
                return []
        _p("Running BLAST search")
        hits = detect_genes(args.input, args.db, args.identity, args.coverage, output_dir=outdir, console=console, rich_enabled=rich_flag, fail_silently=True)
        _p("Filtering hits")
        results = interpret_hits(hits, args.map)
        _p("Building summary")
        write_report(results, os.path.join(outdir, args.output_name), save=not args.summary, console=console, rich_enabled=rich_flag)
        combined_results = results

    # Generate plots if requested
    if args.plot and not args.summary:
        try:
            from visualization import plot_gene_heatmap, plot_class_bar, plot_gene_class_network
            # Pass console if available for progress messages
            _p("Generating plots")
            plot_gene_heatmap(combined_results, filename='gene_heatmap.png', output_dir=outdir, console=console, rich_enabled=rich_flag)
            plot_class_bar(combined_results, filename='class_bar.png', output_dir=outdir, console=console, rich_enabled=rich_flag)
            plot_gene_class_network(combined_results, filename='gene_class_network.png', output_dir=outdir, console=console, rich_enabled=rich_flag)
        except Exception as e:
            logging.warning(f"Visualization failed: {e}")

    _p("Finalizing output")
    return combined_results


def main():
    parser = argparse.ArgumentParser(description="Antibiotic Resistance Gene Detector")
    # Read version from project VERSION file if available
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        with open(os.path.join(project_root, '..', 'VERSION')) as vf:
            version_str = vf.read().strip()
    except Exception:
        try:
            with open(os.path.join(project_root, 'VERSION')) as vf:
                version_str = vf.read().strip()
        except Exception:
            version_str = "0.0.0"
    parser.add_argument("--input", required=True, help="Input FASTA file or directory")
    parser.add_argument("--db", default="AntibioticResistanceGeneDetector/data/resistance_genes.fasta", help="Resistance gene DB FASTA")
    parser.add_argument("--map", default="AntibioticResistanceGeneDetector/data/gene_class_map.csv", help="Gene-to-class CSV mapping")
    parser.add_argument("--outdir", dest='outdir', default="output", help="Directory for CSV, logs, and plots")
    parser.add_argument("--output", dest='output_name', default="results.csv", help="Combined CSV filename")
    parser.add_argument("--identity", type=float, default=90, help="Minimum percent identity (default: 90)")
    parser.add_argument("--coverage", type=int, default=80, help="Minimum alignment coverage in bp (default: 80)")
    parser.add_argument("--threads", type=int, default=1, help="Threads for batch processing (default: 1)")
    parser.add_argument("--plot", action="store_true", help="Save heatmap/bar/network plots")
    parser.add_argument("--summary", action="store_true", help="Print summary only; skip saving CSVs")
    parser.add_argument("--quiet", action="store_true", help="Show only errors (silence info logs)")
    parser.add_argument("--rich", dest='rich', action="store_true", help="Enable Rich terminal output")
    parser.add_argument("--no-rich", dest='rich', action="store_false", help="Disable Rich terminal output")
    parser.add_argument('--version', action='version', version=version_str, help='Show tool version and exit')
    args = parser.parse_args()
    # Backwards compatibility: allow --output as full path when provided earlier
    if os.path.isabs(args.output_name) or os.path.dirname(args.output_name):
        args.outdir = os.path.dirname(args.output_name) or args.outdir
        args.output_name = os.path.basename(args.output_name)
    # Fill default attributes for internal use
    args.threads = args.threads if hasattr(args, 'threads') else 1
    args.plot = args.plot if hasattr(args, 'plot') else False
    args.summary = args.summary if hasattr(args, 'summary') else False
    args.quiet = args.quiet if hasattr(args, 'quiet') else False
    # Rich flag default True unless explicitly set false
    args.rich = True if not hasattr(args, 'rich') else args.rich
    # Run pipeline and handle CLI-level errors with friendly output
    try:
        run_pipeline(args)
    except Exception as e:
        # Try to use rich utils to show a friendly message
        try:
            from src.rich_utils import print_error, get_console
            console = get_console(rich_enabled=getattr(args, 'rich', True), quiet=getattr(args, 'quiet', False))
            print_error(str(e), console=console, rich_enabled=getattr(args, 'rich', True))
        except Exception:
            print(f"ERROR: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
