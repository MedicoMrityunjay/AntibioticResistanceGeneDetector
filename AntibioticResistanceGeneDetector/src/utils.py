"""
Utility helpers for the project: file validation, FASTA parsing,
table formatting and logging setup.

The module contains small, focused helpers that are used by the CLI and
the detection pipeline. They intentionally avoid heavy dependencies at
import time and validate external files robustly.
"""

import os
import logging
from Bio import SeqIO

try:
    from src.rich_utils import setup_rich_logging, get_console
    _HAS_RICH_UTILS = True
except Exception:
    _HAS_RICH_UTILS = False

def setup_logging(quiet: bool = False, log_dir: str = "output/logs"):
    """
    Configure application logging with optional Rich integration.

    Parameters
    ----------
    quiet : bool, optional
        If True, set logging to error-only on the console (default: False).
    log_dir : str, optional
        Directory where rotating or plain log files will be written
        (default: ``output/logs``).

    Returns
    -------
    None
    """
    level = logging.ERROR if quiet else logging.INFO
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "project.log")
    # Remove all handlers to avoid duplicate logs when called multiple times
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)
    # Prefer rich logging handler when available
    try:
        if _HAS_RICH_UTILS:
            setup_rich_logging(rich_enabled=True, quiet=quiet)
            # Add a file handler as well
            fh = logging.FileHandler(log_file, mode="a")
            fh.setLevel(level)
            logging.getLogger().addHandler(fh)
            return
    except Exception:
        pass
    # Fallback basic logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a"),
            logging.StreamHandler()
        ]
    )

def validate_fasta(filepath):
    """
    Validate that a path points to a readable FASTA with plausible sequences.

    The function attempts several candidate locations for the provided
    path (the path as given, relative to the project root, and the basename
    in the project root) before raising a ``MissingFileError``.

    Parameters
    ----------
    filepath : str
        Path to the FASTA file to validate.

    Returns
    -------
    bool
        ``True`` when the file appears to be a valid FASTA with at least one
        reasonable sequence.

    Raises
    ------
    MissingFileError
        If the file cannot be found at any of the candidate locations.
    CorruptedInputError
        If the file is found but cannot be parsed as a FASTA, is empty, or
        contains sequences that do not look like nucleotide sequences.
    """
    from src.error_handling import CorruptedInputError, MissingFileError

    def _resolve_path(p):
        # Try the path as given
        if os.path.exists(p):
            return p
        # Try relative to project root (one level up from src)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        candidate = os.path.join(project_root, p)
        if os.path.exists(candidate):
            return candidate
        # Try basename in project root
        candidate2 = os.path.join(project_root, os.path.basename(p))
        if os.path.exists(candidate2):
            return candidate2
        return p

    filepath = _resolve_path(filepath)
    if not os.path.exists(filepath):
        raise MissingFileError(f"File not found: {filepath}")
    try:
        records = list(SeqIO.parse(filepath, "fasta"))
        if not records:
            raise CorruptedInputError("FASTA file is empty or invalid.")
        # Basic sanity check: ensure sequences look like nucleotides (A/C/G/T/N)
        valid_chars = set(list("ACGTNacgtn"))
        for rec in records:
            seq_chars = set(str(rec.seq))
            # If sequence contains no valid nucleotide letters, treat as corrupted
            if seq_chars.isdisjoint(valid_chars):
                raise CorruptedInputError("FASTA sequences do not appear to be valid nucleotides.")
        return True
    except Exception as e:
        raise CorruptedInputError(f"FASTA validation failed: {e}")

def format_table(rows, headers):
    """
    Format a sequence of mappings as an ASCII table string.

    Parameters
    ----------
    rows : list of dict
        Rows to format. Each row is a mapping from column name to value.
    headers : list of str
        Column order to include in the output string.

    Returns
    -------
    str
        The rendered table as produced by ``pandas.DataFrame.to_string``.
    """
    import pandas as pd
    df = pd.DataFrame(rows)
    return df.to_string(index=False)

def read_gene_class_map(map_path):
    """
    Read a gene-to-class mapping CSV and return a lookup dictionary.

    Parameters
    ----------
    map_path : str
        Path to the CSV file containing columns ``gene`` and ``class``.

    Returns
    -------
    dict
        Mapping from gene identifier to antibiotic class.
    """
    import pandas as pd

    def _resolve_map(p):
        if os.path.exists(p):
            return p
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        candidate = os.path.join(project_root, p)
        if os.path.exists(candidate):
            return candidate
        # Sometimes callers prefix with project folder; strip that
        # Handle possible prefix using either separator
        prefix = 'AntibioticResistanceGeneDetector' + os.sep
        alt_prefix = 'AntibioticResistanceGeneDetector' + '/'
        if p.startswith(prefix):
            stripped = p.split(os.sep, 1)[1]
            candidate2 = os.path.join(project_root, stripped)
            if os.path.exists(candidate2):
                return candidate2
        if p.startswith(alt_prefix):
            stripped = p.split('/', 1)[1]
            candidate2 = os.path.join(project_root, stripped)
            if os.path.exists(candidate2):
                return candidate2
        candidate3 = os.path.join(project_root, os.path.basename(p))
        if os.path.exists(candidate3):
            return candidate3
        return p

    map_path = _resolve_map(map_path)
    df = pd.read_csv(map_path)
    return dict(zip(df['gene'], df['class']))
