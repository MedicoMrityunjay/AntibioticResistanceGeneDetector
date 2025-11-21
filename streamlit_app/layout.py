# streamlit_app/layout.py
"""
Page layout helpers for the Streamlit app.
- Sidebar controls: upload FASTA, set identity, coverage, threads, outdir
- Main area renderer: results table, plots, download buttons, logs.
"""
from pathlib import Path
from typing import Optional
import streamlit as st


def render_sidebar(default_temp_dir: Optional[str] = None) -> dict:
    """Render the sidebar inputs and return a dict of current input values.

    Parameters
    ----------
    default_temp_dir: str
        Default path to use for outputs if the user doesn't specify

    Returns
    -------
    dict
        keys: uploaded_files, fasta_dir, db_path, gene_map, identity, coverage, threads, outdir, run
    """
    st.sidebar.header("Inputs")

    uploaded_files = st.sidebar.file_uploader(
        "Upload FASTA file(s)", type=["fa", "fasta", "fas", "fna"], accept_multiple_files=True
    )

    fasta_dir = st.sidebar.text_input("(Optional) FASTA input directory", value="")

    db_path = st.sidebar.text_input("Resistance genes DB path", value="")
    gene_map = st.sidebar.text_input("Gene class map CSV path", value="")

    identity = st.sidebar.number_input("Minimum percent identity", min_value=50.0, max_value=100.0, value=90.0, help="Minimum percent identity (50-100)")
    coverage = st.sidebar.number_input("Minimum percent coverage", min_value=10.0, max_value=100.0, value=80.0, help="Minimum percent coverage (10-100)")
    threads = st.sidebar.number_input("Threads", min_value=1, max_value=32, value=1, help="CPU threads to use (1-32)")

    # run_pipeline flags
    plot = st.sidebar.checkbox("Generate plots (plot)", value=True)
    summary = st.sidebar.checkbox("Summary mode (no CSVs written)", value=False)
    quiet = st.sidebar.checkbox("Quiet output (quiet)", value=False)
    rich = st.sidebar.checkbox("Enable Rich output (rich)", value=True)
    mock_mode = st.sidebar.checkbox("Mock Mode (no BLAST)", value=False)

    outdir = st.sidebar.text_input("Output directory", value=default_temp_dir or "")

    run = st.sidebar.button("Run detection")

    return {
        "uploaded_files": uploaded_files,
        "fasta_dir": fasta_dir or None,
        "db_path": db_path or None,
        "gene_map": gene_map or None,
        "identity": float(identity),
        "coverage": float(coverage),
        "threads": int(threads),
        "plot": bool(plot),
        "summary": bool(summary),
        "quiet": bool(quiet),
        "rich": bool(rich),
        "mock_mode": bool(mock_mode),
        "outdir": outdir or default_temp_dir,
        "run": run,
    }


def render_main_area(results: dict | None):
    """Render the main results area.

    Parameters
    ----------
    results : dict | None
        The dictionary returned by the handler with keys like `dataframe`, `plots`, `csv_path`, `logs`.
    """
    st.header("Results")

    if results is None:
        st.info("No results yet. Configure inputs in the sidebar and click Run detection.")
        return

    # If the handler returned a status indicating failure, show message and logs
    status = results.get("status")
    if status and status != "COMPLETED":
        st.error(results.get("message") or "Run failed")
        logs = results.get("logs")
        if logs:
            with st.expander("Logs"):
                st.code(logs)
        # still continue to show any partial dataframe or results

    df = results.get("dataframe")
    if df is not None:
        st.subheader("Results table")
        st.dataframe(df)

        csv_bytes = results.get("csv_bytes")
        if csv_bytes:
            st.download_button("Download CSV", data=csv_bytes, file_name="results.csv", mime="text/csv")

        # Inform user when mock mode was used
        if results.get("mock"):
            st.warning("Mock mode active, no real gene detection performed")

    plots = results.get("plots", [])
    if plots:
        st.subheader("Plots")
        for p in plots:
            st.image(p, use_column_width=True)

        # Download all plots as a zip if available
        zip_bytes = results.get("plots_zip")
        if zip_bytes:
            st.download_button("Download plots (zip)", data=zip_bytes, file_name="plots.zip")

    logs = results.get("logs")
    if logs:
        with st.expander("Logs"):
            st.code(logs)
    # Show fallback banner when handlers signalled fallback_to_mock
    if results.get("fallback_to_mock"):
        st.warning("BLAST/DIAMOND not found — app fell back to MOCK MODE for this run.")

    # Show progress updates collected by the handler (if any)
    progress_updates = results.get("progress_updates") or []
    if progress_updates:
        with st.expander("Progress updates"):
            for m in progress_updates:
                st.write(m)
