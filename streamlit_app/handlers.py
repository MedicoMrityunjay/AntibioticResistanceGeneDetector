"""
Handlers for Streamlit app: save uploads, run pipeline (or mock), collect outputs.

This minimal implementation is intentionally conservative so it is easy to
maintain while we finalize worker/job_manager changes.
"""

from pathlib import Path
from typing import List, Callable, Optional
import argparse
import traceback
import time
import pandas as pd

from utils import save_uploaded_files, find_results_csv, find_plot_files, zip_files_to_bytes, validate_fasta

HERE = Path(__file__).resolve().parent
LOGS_DIR = HERE / "temp" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Import pipeline entrypoint if available
try:
    from src.main import run_pipeline
except Exception:
    run_pipeline = None


def _failure(message: str, tb: Optional[str] = None, fallback_to_mock: bool = False):
    return {
        "status": "FAILED",
        "message": message,
        "logs": tb or "",
        "results_object": [],
        "fallback_to_mock": bool(fallback_to_mock),
        "last_error": tb,
    }


def run_detection_and_collect(uploaded_files, fasta_dir, db_path, gene_map, identity, coverage, threads, outdir, temp_dir: Path, plot: bool = True, summary: bool = False, quiet: bool = False, rich: bool = True, mock_mode: bool = False, progress_callback: Optional[Callable[[str], None]] = None):
    """Save uploads, optionally run pipeline, and collect outputs.

    Returns a standardized dict with keys: status, message, results_object, and
    optional artifacts (dataframe, csv_bytes, plots, plots_zip, logs).
    """
    temp_dir = Path(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    input_dir = temp_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    # Persist uploaded files
    try:
        _ = save_uploaded_files(uploaded_files, input_dir, allowed_extensions=[".fa", ".fasta", ".fas", ".fna"])
    except Exception:
        tb = traceback.format_exc()
        return _failure("Failed saving uploaded files", tb=tb)

    # Mock mode or pipeline unavailable -> return small fabricated result
    if mock_mode or run_pipeline is None:
        df = pd.DataFrame([{"sample": "mock1", "gene": "MOCK_GENE_A", "identity": 99.0}])
        return {
            "status": "COMPLETED",
            "message": "Mock run completed",
            "dataframe": df,
            "csv_bytes": df.to_csv(index=False).encode("utf-8"),
            "results_object": df.to_dict(orient="records"),
            "plots": [],
            "plots_zip": b"",
            "logs": "MOCK MODE",
            "fallback_to_mock": True,
            "last_error": None,
        }

    # Build args similar to CLI
    args = argparse.Namespace()
    args.input = str(input_dir)
    args.db = str(db_path) if db_path else None
    args.map = str(gene_map) if gene_map else None
    args.outdir = str(outdir) if outdir else str(temp_dir / "out")
    args.output_name = "results.csv"
    args.identity = float(identity) if identity is not None else 90.0
    args.coverage = int(coverage) if coverage is not None else 80
    args.threads = int(threads) if threads is not None else 1
    args.plot = bool(plot)
    args.summary = bool(summary)
    args.quiet = bool(quiet)
    args.rich = bool(rich)

    # Execute pipeline
    try:
        results = run_pipeline(args, progress=progress_callback) if run_pipeline else []
    except Exception:
        tb = traceback.format_exc()
        return _failure("Pipeline execution failed", tb=tb)

    # Collect outputs
    outdir_path = Path(args.outdir)
    csvs = find_results_csv(outdir_path)
    plot_files = find_plot_files(outdir_path)

    df = None
    csv_bytes = None
    if csvs:
        try:
            df = pd.read_csv(csvs[0])
            csv_bytes = df.to_csv(index=False).encode("utf-8")
        except Exception:
            try:
                csv_bytes = Path(csvs[0]).read_bytes()
            except Exception:
                csv_bytes = None

    plots_zip = None
    if plot_files:
        try:
            plots_zip = zip_files_to_bytes(plot_files)
        except Exception:
            plots_zip = None

    return {
        "status": "COMPLETED",
        "message": "Run completed",
        "dataframe": df,
        "csv_bytes": csv_bytes,
        "plots": [str(p) for p in plot_files] if plot_files else [],
        "plots_zip": plots_zip,
        "logs": "",
        "csv_paths": [str(p) for p in csvs] if csvs else [],
        "results_object": results or [],
        "progress_updates": [],
        "fallback_to_mock": False,
        "last_error": None,
    }
