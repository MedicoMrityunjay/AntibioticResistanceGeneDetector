"""
Interpretation and reporting helpers.

This module maps detected gene identifiers to antibiotic classes using a
CSV lookup and provides a small reporting helper that writes CSV output
and prints a human-friendly summary table (optionally using Rich).
"""

import os
import logging
import pandas as pd
from src.utils import read_gene_class_map, format_table
try:
    from rich.table import Table
    from src.rich_utils import get_console
    _HAS_RICH = True
except Exception:
    _HAS_RICH = False

def interpret_hits(hits, map_path):
    """
    Map gene hit records to antibiotic classes using a CSV mapping.

    Parameters
    ----------
    hits : list of dict
        Hit dictionaries produced by the detection stage (must include
        at least keys ``gene`` and optionally ``sample_id`` and ``length``).
    map_path : str
        Path to a CSV file containing columns ``gene`` and ``class``.

    Returns
    -------
    list of dict
        Each record is annotated with ``antibiotic_class`` and includes
        the original sample and source information where available.
    """
    gene_class = read_gene_class_map(map_path)
    results = []
    for hit in hits:
        gene = hit["gene"]
        results.append({
            "sample_id": hit.get("sample_id", "sample"),
            "gene": gene,
            "identity": hit["identity"],
            "coverage": hit["length"],
            "antibiotic_class": gene_class.get(gene, "Unknown"),
            "class": gene_class.get(gene, "Unknown"),
            "source_file": hit.get("source_file", "")
        })
    return results

def write_report(results, output_path="output/results.csv", save: bool = True, console=None, rich_enabled: bool = True):
    """
    Write interpreted results to CSV and print a summary table.

    Parameters
    ----------
    results : list of dict
        Interpreted result dictionaries (see :func:`interpret_hits`).
    output_path : str, optional
        Destination CSV path for the combined results (default: ``output/results.csv``).
    save : bool, optional
        If ``False`` the CSV will not be written; the summary will still be printed.
    console : Console-like, optional
        Optional console for Rich output. If not provided and Rich is
        available, a console will be created.
    rich_enabled : bool, optional
        Whether to use Rich-based formatting when available (default: True).

    Returns
    -------
    None
    """
    import pandas as pd
    columns = ["sample_id", "gene", "identity", "coverage", "antibiotic_class", "source_file"]
    df = pd.DataFrame(results, columns=columns) if len(results) > 0 else pd.DataFrame(columns=columns)
    if save:
        # Ensure directory exists
        outdir = os.path.dirname(output_path)
        if outdir:
            os.makedirs(outdir, exist_ok=True)
        df.to_csv(output_path, index=False)
        logging.info("Results written to %s", output_path)
    # If rich is requested and available, use Rich Table; otherwise plain text
    if rich_enabled and _HAS_RICH:
        if console is None:
            # create a rich console (not quiet)
            try:
                from src.rich_utils import get_console
                console = get_console(rich_enabled=True, quiet=False)
            except Exception:
                console = None
        if console is not None:
            console.rule("Summary Table")
            if df.empty:
                console.print("No resistance genes detected in any sample.")
            else:
                table = Table(show_header=True, header_style="bold magenta")
                for col in columns:
                    table.add_column(col)
                for _, row in df.iterrows():
                    table.add_row(*[str(row[col]) if not pd.isna(row[col]) else "" for col in columns])
                console.print(table)
            return

    # Fallback plain text output
    print("\nSummary Table:")
    if df.empty:
        print("No resistance genes detected in any sample.")
    else:
        print(df.to_string(index=False, columns=columns))
