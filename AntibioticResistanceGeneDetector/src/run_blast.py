"""
BLAST/DIAMOND wrapper for resistance gene detection.

Provides helpers for invoking DIAMOND or BLAST+ tools (when available)
and a lightweight mock search used for testing or when external tools
are not present. The module normalizes tabular output into a unified
list-of-dicts structure consumed by the rest of the pipeline.
"""
import logging
import os
import subprocess
try:
    from src.rich_utils import get_progress
    _HAS_RICH = True
except Exception:
    _HAS_RICH = False


def run_blast(query_fasta, db_fasta, identity=90, coverage=80, max_targets=10, tool=None, console=None, rich_enabled: bool = True):
    """
    Run DIAMOND (preferred), BLAST+, or a mock search and parse results.

    Parameters
    ----------
    query_fasta : str
        Path to the query FASTA file.
    db_fasta : str
        Path to the resistance gene database FASTA.
    identity : float, optional
        Minimum percent identity for reported hits (default: 90).
    coverage : int, optional
        Minimum alignment length / coverage for reported hits (default: 80).
    max_targets : int, optional
        Maximum number of target hits to request from the search tool.
    tool : str or None, optional
        Force a particular tool (e.g. 'diamond' or 'blastn'). When ``None``
        the function will auto-detect an available search tool.
    console : object, optional
        Optional console-like object used to display Rich progress/status.
    rich_enabled : bool, optional
        Whether to attempt Rich-based output when available (default: True).

    Returns
    -------
    list of dict
        Normalized list of hit dictionaries as produced by
        :func:`parse_blast_results` or by the internal mock search.
    """
    out_file = "output/blast_results.tsv"
    tool = detect_search_tool()
    if tool == "diamond":
        verify_diamond_db(db_fasta)
        cmd = [
            "diamond", "blastx",
            "-q", query_fasta,
            "-d", db_fasta,
            "-o", out_file,
            "--outfmt", "6 qseqid sseqid pident length qstart qend sstart send",
            "--max-target-seqs", str(max_targets)
        ]
    elif tool in ["blastn", "blastp"]:
        verify_blast_db(db_fasta, tool)
        cmd = [
            tool,
            "-query", query_fasta,
            "-db", db_fasta,
            "-outfmt", "6 qseqid sseqid pident length qstart qend sstart send",
            "-max_target_seqs", str(max_targets),
            "-out", out_file
        ]
    else:
        logging.warning("BLAST/DIAMOND not found, using mock search.")
        return mock_search(query_fasta, db_fasta)
    try:
        # If rich progress is available, show a spinner/status via console
        if console is not None and _HAS_RICH and rich_enabled:
            try:
                with console.status(f"Running {tool} on {os.path.basename(query_fasta)}..."):
                    subprocess.run(cmd, check=True)
            except Exception:
                subprocess.run(cmd, check=True)
        else:
            subprocess.run(cmd, check=True)
        logging.info(f"{tool} search completed: {out_file}")
        return parse_blast_results(out_file, identity, coverage)
    except Exception as e:
        logging.error(f"{tool} search failed: {e}")
        return []

def detect_search_tool():
    """
    Detect an available sequence search tool on PATH.

    Checks for DIAMOND first (preferred), then BLAST+ programs in a
    conservative order. This helper returns the short tool name or
    ``None`` if no tool is found.

    Returns
    -------
    str or None
        One of ``'diamond'``, ``'blastn'``, ``'blastp'`` or ``None``.
    """
    if is_tool_installed("diamond"):
        return "diamond"
    elif is_tool_installed("blastn"):
        return "blastn"
    elif is_tool_installed("blastp"):
        return "blastp"
    return None

def verify_blast_db(db_fasta, tool):
    """
    Ensure a BLAST+ database exists for ``db_fasta`` and create it if not.

    Parameters
    ----------
    db_fasta : str
        Path to the FASTA file used as input to ``makeblastdb``.
    tool : str
        BLAST program name (``'blastn'`` or other) used to determine DB type.

    Returns
    -------
    None

    Raises
    ------
    subprocess.CalledProcessError
        If ``makeblastdb`` fails when invoked.
    """
    db_files = [db_fasta + ext for ext in [".nin", ".nhr", ".nsq"]] if tool == "blastn" else [db_fasta + ext for ext in [".pin", ".phr", ".psq"]]
    if not all(os.path.exists(f) for f in db_files):
        logging.info(f"BLAST DB not found for {db_fasta}, creating with makeblastdb.")
        db_type = "nucl" if tool == "blastn" else "prot"
        cmd = ["makeblastdb", "-in", db_fasta, "-dbtype", db_type]
        subprocess.run(cmd, check=True)

def verify_diamond_db(db_fasta):
    """
    Ensure a DIAMOND database exists for ``db_fasta`` and create it if not.

    Parameters
    ----------
    db_fasta : str
        Path to the FASTA file used to create a DIAMOND database (.dmnd).

    Returns
    -------
    None
    """
    dmnd_file = db_fasta + ".dmnd"
    if not os.path.exists(dmnd_file):
        logging.info(f"DIAMOND DB not found for {db_fasta}, creating with diamond makedb.")
        cmd = ["diamond", "makedb", "--in", db_fasta, "-d", db_fasta]
        subprocess.run(cmd, check=True)

def is_tool_installed(tool_name):
    """
    Check whether an executable is available on the system PATH.

    Parameters
    ----------
    tool_name : str
        Executable name to look for in PATH.

    Returns
    -------
    bool
        ``True`` if the executable is found, ``False`` otherwise.
    """
    from shutil import which
    return which(tool_name) is not None

def parse_blast_results(tsv_path, identity, coverage):
    """
    Parse tabular BLAST/DIAMOND output into a list of result dictionaries.

    Parameters
    ----------
    tsv_path : str
        Path to the tabular output file in BLAST/DIAMOND "outfmt 6" format.
    identity : float
        Minimum percent identity threshold for accepting hits.
    coverage : int
        Minimum alignment length (coverage) in base pairs/residues.

    Returns
    -------
    list of dict
        Each dict contains keys: ``query``, ``gene``, ``identity``, ``length``,
        ``qstart``, ``qend``, ``sstart``, ``send``.
    """
    results = []
    if not os.path.exists(tsv_path):
        return results
    with open(tsv_path) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 8:
                continue
            qseqid, sseqid, pident, length, qstart, qend, sstart, send = parts[:8]
            pident = float(pident)
            length = int(length)
            if pident >= identity and length >= coverage:
                results.append({
                    "query": qseqid,
                    "gene": sseqid,
                    "identity": pident,
                    "length": length,
                    "qstart": int(qstart),
                    "qend": int(qend),
                    "sstart": int(sstart),
                    "send": int(send)
                })
    return results

def mock_search(query_fasta, db_fasta):
    """
    A deterministic fallback search used when external tools are absent.

    This function iterates over the records in ``db_fasta`` and returns a
    hit for each gene with 100% identity and full-length coverage. It is
    useful for unit tests and demonstration runs.

    Parameters
    ----------
    query_fasta : str
        Path to the query FASTA (not used for matching in the mock, but kept
        for API compatibility).
    db_fasta : str
        Path to the database FASTA whose records will be returned as hits.

    Returns
    -------
    list of dict
        Match entries in the same normalized format as produced by the
        real BLAST/DIAMOND parser.
    """
    from Bio import SeqIO
    results = []
    for record in SeqIO.parse(db_fasta, "fasta"):
        results.append({
            "query": "mock_query",
            "gene": record.id,
            "identity": 100.0,
            "length": len(record.seq),
            "qstart": 1,
            "qend": len(record.seq),
            "sstart": 1,
            "send": len(record.seq)
        })
    return results
