"""
Gene detection helpers.

This module exposes functions to run similarity searches on input FASTA
files, extract best hits per gene, and process directories of FASTA files
in batch. The functions return normalized hit dictionaries compatible with
the interpreter and reporting utilities.
"""
from src.utils import validate_fasta
from src.run_blast import run_blast
from src.error_handling import NoHitsFoundError, safe_fail
import os
import logging
try:
    from src.rich_utils import get_progress
    _HAS_RICH = True
except Exception:
    _HAS_RICH = False

def detect_genes(input_fasta, db_fasta, identity=90, coverage=80, sample_id=None, output_dir="output", console=None, rich_enabled: bool = True, fail_silently: bool = False):
    """
    Detect resistance genes in a single input FASTA.

    The function validates the input and database FASTA files, runs a
    similarity search (via :func:`run_blast`), selects the best hit per
    detected gene, and annotates each hit with ``sample_id``.

    Parameters
    ----------
    input_fasta : str
        Path to the FASTA file containing query sequences.
    db_fasta : str
        Path to the resistance gene database FASTA.
    identity : float, optional
        Minimum percent identity to accept a hit (default: 90).
    coverage : int, optional
        Minimum alignment length/coverage to accept a hit (default: 80).
    sample_id : str, optional
        Identifier to add to returned hit records. When omitted the
        basename of ``input_fasta`` is used.
    output_dir : str, optional
        Directory used for per-sample output files when writing safe-fail
        reports (default: ``output``).
    console : object, optional
        Console-like object for status messages (Rich or dummy console).
    rich_enabled : bool, optional
        Whether to attempt Rich-based output when available (default: True).
    fail_silently : bool, optional
        When True, write a minimal error report on error and return an
        empty list instead of raising.

    Returns
    -------
    list of dict
        Selected best-hit records for the sample with ``sample_id`` added.
    """
    # Added fail_silently option
    try:
        # Validate input FASTA first; let input-related errors propagate
        if console is not None and rich_enabled:
            with console.status(f"Validating input FASTA {input_fasta}..."):
                validate_fasta(input_fasta)
        else:
            validate_fasta(input_fasta)

        # Validate DB FASTA; if DB missing or corrupted, safe-fail the sample (do not raise)
        try:
            if console is not None and rich_enabled:
                with console.status(f"Validating DB FASTA {db_fasta}..."):
                    validate_fasta(db_fasta)
            else:
                validate_fasta(db_fasta)
        except Exception as db_e:
            # If caller requested silent failure for DB issues, write safe-fail and return empty
            out_name = f"{sample_id if sample_id else os.path.splitext(os.path.basename(input_fasta))[0]}_results.csv"
            out_path = os.path.join(output_dir, out_name)
            safe_fail(str(db_e), output_path=out_path)
            return []

        hits = run_blast(input_fasta, db_fasta, identity, coverage, console=console, rich_enabled=rich_enabled)
        if not hits:
            raise NoHitsFoundError("No resistance genes detected.")
        best_hits = {}
        for hit in hits:
            gene = hit["gene"]
            if gene not in best_hits or hit["identity"] > best_hits[gene]["identity"]:
                best_hits[gene] = hit
        for hit in best_hits.values():
            hit["sample_id"] = sample_id if sample_id else os.path.basename(input_fasta)
        logging.info(f"Detected {len(best_hits)} resistance genes for sample {sample_id if sample_id else input_fasta}.")
        return list(best_hits.values())
    except Exception as e:
        if fail_silently:
            out_name = f"{sample_id if sample_id else os.path.splitext(os.path.basename(input_fasta))[0]}_results.csv"
            out_path = os.path.join(output_dir, out_name)
            safe_fail(str(e), output_path=out_path)
            return []
        else:
            raise

def batch_detect_genes(input_folder, db_fasta, identity=90, coverage=80, threads: int = 1, output_dir: str = "output", write_per_sample: bool = True, console=None, rich_enabled: bool = True):
    """
    Process all FASTA files under ``input_folder`` and return hits per sample.

    The function walks the directory tree, validates FASTA files, and
    dispatches processing either sequentially or using a thread pool when
    ``threads`` &gt; 1. Returned structure is a mapping ``{sample_id: hits}``.

    Parameters
    ----------
    input_folder : str
        Path to the folder containing FASTA files (recursively searched).
    db_fasta : str
        Path to the resistance gene database FASTA.
    identity : float, optional
        Minimum percent identity to accept a hit (default: 90).
    coverage : int, optional
        Minimum alignment coverage (default: 80).
    threads : int, optional
        Number of worker threads for concurrent processing (default: 1).
    output_dir : str, optional
        Directory to write per-sample outputs and logs (default: ``output``).
    write_per_sample : bool, optional
        If True, callers may save per-sample CSV files (default: True).
    console : object, optional
        Console-like object for progress/status messages.
    rich_enabled : bool, optional
        Whether to use Rich-based progress when available.

    Returns
    -------
    dict
        Mapping of sample identifier to list of hit dictionaries.
    """
    import os
    import glob
    from src.utils import validate_fasta
    results = {}
    # Recursively find all .fasta files
    fasta_files = [y for x in os.walk(input_folder) for y in glob.glob(os.path.join(x[0], '*.fasta'))]

    def _process(fasta):
        sample_id = os.path.splitext(os.path.basename(fasta))[0]
        try:
            validate_fasta(fasta)
            hits = detect_genes(fasta, db_fasta, identity, coverage, sample_id=sample_id, output_dir=output_dir, console=None, rich_enabled=rich_enabled, fail_silently=True)
            for hit in hits:
                hit['source_file'] = os.path.relpath(fasta)
            return sample_id, hits
        except Exception as e:
            import logging
            logging.warning(f"Skipping file {fasta}: {e}")
            return sample_id, []

    # If rich progress is available and console provided, show progress
    progress_ctor = get_progress(rich_enabled=rich_enabled) if _HAS_RICH else None
    if threads and threads > 1:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
            future_to_fasta = {ex.submit(_process, f): f for f in fasta_files}
            if progress_ctor and console is not None:
                with progress_ctor as progress:
                    task = progress.add_task("Processing FASTA files...", total=len(future_to_fasta))
                    for fut in concurrent.futures.as_completed(future_to_fasta):
                        sample_id, hits = fut.result()
                        results[sample_id] = hits
                        progress.advance(task)
            else:
                for fut in concurrent.futures.as_completed(future_to_fasta):
                    sample_id, hits = fut.result()
                    results[sample_id] = hits
    else:
        if progress_ctor and console is not None:
            with progress_ctor as progress:
                for fasta in progress.track(fasta_files, description="Processing FASTA files..."):
                    sample_id, hits = _process(fasta)
                    results[sample_id] = hits
        else:
            for fasta in fasta_files:
                sample_id, hits = _process(fasta)
                results[sample_id] = hits

    # Return results dict; caller may write per-sample CSVs
    return results
