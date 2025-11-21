# streamlit_app/app.py
"""
Main Streamlit app for running the AntibioticResistanceGeneDetector pipeline.
- Sidebar controls for inputs (FASTA upload, DB, gene map, identity, coverage, threads, outdir)
- Main area shows results table, plots, logs, and About/version information

This file does not implement detection logic — it uses helpers in `handlers.py` which call
`run_pipeline()` from `src.main` and visualization helpers from `src.visualization`.
"""
from pathlib import Path
import sys
import shutil
import streamlit as st

# Ensure project package path is available for imports used by handlers/layout
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
PROJECT_PKG_PATH = PROJECT_ROOT / "AntibioticResistanceGeneDetector"
if str(PROJECT_PKG_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PKG_PATH))

from layout import render_sidebar, render_main_area
from handlers import run_detection_and_collect
from utils import read_version_safe
from job_manager import create_job, list_jobs, update_job
import threading
from job_worker import run_worker_loop
import json
import time
import os
from pathlib import Path
import streamlit.components.v1 as components

# --- Persistent worker start (safe across Streamlit reruns) ---
if "worker_started" not in st.session_state:
    t_worker = threading.Thread(target=run_worker_loop, kwargs={"poll_interval": 2}, daemon=True)
    t_worker.start()
    st.session_state["worker_started"] = True
# --- End worker bootstrap ---

st.set_page_config(page_title="Antibiotic Resistance Gene Detector", layout="wide")

# App-level temp directory (under streamlit_app/temp)
APP_TEMP = HERE / "temp"
APP_TEMP.mkdir(parents=True, exist_ok=True)

VERSION = read_version_safe(PROJECT_ROOT / "AntibioticResistanceGeneDetector" / "VERSION")


def main():
    st.title("Antibiotic Resistance Gene Detector — Streamlit UI")

    # Sidebar: inputs (only expose real run_pipeline params)
    inputs = render_sidebar(default_temp_dir=str(APP_TEMP))

    # About area in sidebar
    with st.sidebar.expander("About"):
        st.markdown(f"**Version:** {VERSION}")
        st.markdown("Streamlit demo frontend for the detection pipeline. Detection runs on the server where Streamlit is launched.")

    # Run button handling
    tabs = st.tabs(["Run", "Job Queue", "System Status"])

    with tabs[0]:
        # Run tab
        if inputs.get("run"):
            # Run pipeline or submit as a background job
            submit_as_job = st.sidebar.checkbox("Submit as background job", value=False)

            if submit_as_job:
                # persist uploaded files meta and parameters and create job
                uploaded = []
                for u in inputs.get("uploaded_files") or []:
                    uploaded.append({"name": getattr(u, "name", "upload" )})
                params = {
                    "db_path": inputs.get("db_path"),
                    "gene_map": inputs.get("gene_map"),
                    "identity": inputs.get("identity"),
                    "coverage": inputs.get("coverage"),
                    "threads": inputs.get("threads"),
                    "plot": bool(inputs.get("plot")),
                    "summary": bool(inputs.get("summary")),
                    "quiet": bool(inputs.get("quiet")),
                    "rich": bool(inputs.get("rich")),
                    "mock_mode": bool(inputs.get("mock_mode")),
                }
                job_id = create_job(uploaded, params)
                st.success(f"Job submitted: {job_id}")
                # spawn a background thread to process immediately
                def _process_job(jid, inputs_local):
                    update_job(jid, status="RUNNING", progress="Job started")
                    # Save uploaded files to job dir
                    job_dir = Path(__file__).resolve().parent / "temp" / "jobs" / jid
                    job_dir.mkdir(parents=True, exist_ok=True)
                    input_path = job_dir / "input"
                    input_path.mkdir(parents=True, exist_ok=True)
                    # save files
                    for u in inputs_local.get("uploaded_files") or []:
                        try:
                            fname = getattr(u, "name", f"upload_{int(time.time())}.fasta")
                            dest = input_path / fname
                            data = None
                            try:
                                data = u.getvalue()
                            except Exception:
                                data = u.read()
                            if isinstance(data, str):
                                data = data.encode("utf-8")
                            dest.write_bytes(data)
                        except Exception as e:
                            update_job(jid, status="FAILED", progress=f"Failed saving upload: {e}")
                            # persist traceback to job log
                            try:
                                import traceback as _tb
                                lf = job_dir / "job_error.log"
                                lf.write_text(_tb.format_exc())
                            except Exception:
                                pass
                            return
                    # Call handler (with robust exception handling)
                    def _progress_hook(m: str):
                        try:
                            update_job(jid, progress=m)
                        except Exception:
                            pass

                    try:
                        res = run_detection_and_collect(
                            uploaded_files=None,
                            fasta_dir=str(input_path),
                            db_path=inputs_local.get("db_path"),
                            gene_map=inputs_local.get("gene_map"),
                            identity=inputs_local.get("identity"),
                            coverage=inputs_local.get("coverage"),
                            threads=inputs_local.get("threads"),
                            outdir=str(job_dir / "out"),
                            temp_dir=job_dir / "temp",
                            plot=bool(inputs_local.get("plot")),
                            summary=bool(inputs_local.get("summary")),
                            quiet=bool(inputs_local.get("quiet")),
                            rich=bool(inputs_local.get("rich")),
                            mock_mode=bool(inputs_local.get("mock_mode")),
                            progress_callback=_progress_hook
                        )
                    except Exception as exc:
                        # mark job failed and save traceback
                        try:
                            import traceback as _tb
                            lf = job_dir / "job_error.log"
                            lf.write_text(_tb.format_exc())
                        except Exception:
                            pass
                        update_job(jid, status="FAILED", progress=str(exc))
                        return

                    # Save results files if present
                    try:
                        if res and res.get("csv_bytes"):
                            (job_dir / "results.csv").write_bytes(res.get("csv_bytes"))
                            update_job(jid, result_files={"csv": str(job_dir / "results.csv")})
                        if res and res.get("plots_zip"):
                            (job_dir / "plots.zip").write_bytes(res.get("plots_zip"))
                            update_job(jid, result_files={"plots": str(job_dir / "plots.zip")})
                    except Exception as e:
                        update_job(jid, progress=f"Failed saving results: {e}")
                    update_job(jid, status="COMPLETED", progress="Job completed")

                import time
                t = threading.Thread(target=_process_job, args=(job_id, {
                    "uploaded_files": inputs.get("uploaded_files"),
                    "db_path": inputs.get("db_path"),
                    "gene_map": inputs.get("gene_map"),
                    "identity": inputs.get("identity"),
                    "coverage": inputs.get("coverage"),
                    "threads": inputs.get("threads"),
                    "plot": inputs.get("plot"),
                    "summary": inputs.get("summary"),
                    "quiet": inputs.get("quiet"),
                    "rich": inputs.get("rich"),
                    "mock_mode": inputs.get("mock_mode"),
                }))
                t.daemon = True
                t.start()
            else:
                # Run in foreground with progress
                pass
        # Foreground run (the original behavior)
        if not st.session_state.get("submitted_job"):
            # When not submitting as job, run immediately as before
            if not st.sidebar.checkbox("Submit as background job", value=False):
                # Prepare UI placeholders for live progress
                progress_container = st.empty()
                progress_bar = st.progress(0)
                progress_messages = []

                def progress_cb(msg: str):
                    progress_messages.append(msg)
                    try:
                        progress_container.text("\n".join(progress_messages[-8:]))
                        progress_bar.progress(min(100, len(progress_messages) * 10))
                    except Exception:
                        pass

                with st.spinner("Running detection pipeline — this may take a while"):
                    results = run_detection_and_collect(
                        uploaded_files=inputs.get("uploaded_files"),
                        fasta_dir=inputs.get("fasta_dir"),
                        db_path=inputs.get("db_path"),
                        gene_map=inputs.get("gene_map"),
                        identity=inputs.get("identity"),
                        coverage=inputs.get("coverage"),
                        threads=inputs.get("threads"),
                        outdir=inputs.get("outdir"),
                        temp_dir=APP_TEMP,
                        plot=bool(inputs.get("plot")),
                        summary=bool(inputs.get("summary")),
                        quiet=bool(inputs.get("quiet")),
                        rich=bool(inputs.get("rich")),
                        mock_mode=bool(inputs.get("mock_mode")),
                        progress_callback=progress_cb,
                    )

                results_progress = results.get("progress_updates") or []
                if results_progress:
                    with st.expander("Progress updates"):
                        for m in results_progress:
                            st.write(m)

                render_main_area(results)
    
    with tabs[1]:
        st.header("Job Queue")
        jobs = list_jobs()
        if not jobs:
            st.info("No jobs submitted yet.")
        else:
            for j in jobs:
                st.subheader(f"Job {j['id']} — {j.get('status')}")
                st.write(f"Created: {j.get('created_at')}")
                st.write("Parameters:")
                st.json(j.get('parameters'))
                # Cancel button for queued or running jobs
                if j.get('status') in ("QUEUED", "RUNNING"):
                    if st.button(f"Cancel {j['id']}", key=f"cancel_{j['id']}"):
                        try:
                            update_job(j['id'], status="CANCELLED", progress="Cancelled by user")
                            st.success(f"Job {j['id']} cancelled")
                        except Exception as e:
                            st.error(f"Failed to cancel job: {e}")
                rf = j.get('result_files') or {}
                if rf:
                    if rf.get('csv'):
                        path = rf.get('csv')
                        try:
                            with open(path, 'rb') as fh:
                                st.download_button(f"Download CSV ({j['id']})", data=fh.read(), file_name=f"{j['id']}_results.csv")
                        except Exception:
                            st.write(f"CSV not available: {path}")
                    if rf.get('plots'):
                        path = rf.get('plots')
                        try:
                            with open(path, 'rb') as fh:
                                st.download_button(f"Download plots ({j['id']})", data=fh.read(), file_name=f"{j['id']}_plots.zip")
                        except Exception:
                            st.write(f"Plots not available: {path}")

        # Job Queue tab only shows listings and downloads; processing runs in background threads

    with tabs[2]:
        st.header("System Status")
        hb_path = HERE / "temp" / "worker.heartbeat.json"
        logs_dir = HERE / "temp" / "logs"
        worker_log = logs_dir / "worker.log"
        pid_file = HERE / "temp" / "worker.pid"

        # Auto-refresh controls
        st.sidebar.markdown("**System Status Refresh**")
        ar = st.sidebar.checkbox("Auto-refresh", key="sys_auto_refresh", value=False)
        auto_interval = st.sidebar.selectbox("Interval (seconds)", [5, 10, 30, 60], index=1, key="sys_auto_interval")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Heartbeat")
            # PID liveness
            if pid_file.exists():
                try:
                    pid_text = pid_file.read_text(encoding="utf-8").strip()
                    pid_val = int(pid_text)
                except Exception:
                    pid_val = None
            else:
                pid_val = None

            alive = None
            if pid_val:
                try:
                    import psutil

                    alive = psutil.pid_exists(pid_val)
                except Exception:
                    try:
                        # fallback to os.kill(0)
                        os.kill(pid_val, 0)
                        alive = True
                    except Exception:
                        alive = False

            if pid_val:
                if alive:
                    st.success(f"Worker PID {pid_val} is running")
                else:
                    st.error(f"Worker PID {pid_val} not running")
            else:
                st.info("No worker PID file found")

            if hb_path.exists():
                try:
                    hb = json.loads(hb_path.read_text(encoding="utf-8"))
                    st.json(hb)
                except Exception as e:
                    st.error(f"Failed reading heartbeat: {e}")
            else:
                st.info("No heartbeat file found. Worker may not be running.")

            if st.button("Refresh Status"):
                st.experimental_rerun()

        with col2:
            st.subheader("Worker Log (tail)")
            if worker_log.exists():
                try:
                    # show last ~200 lines
                    data = worker_log.read_text(encoding="utf-8")
                    lines = data.splitlines()
                    tail = "\n".join(lines[-200:])
                    st.code(tail)
                except Exception as e:
                    st.error(f"Failed reading log: {e}")
            else:
                st.info("Worker log not found.")

        # Inject an auto-refresh script if enabled
        if ar:
            try:
                interval_ms = int(auto_interval) * 1000
                # Use a one-shot timeout so the client reloads and the server-side session_state persists
                components.html(f"<script>setTimeout(()=>{{window.location.reload();}}, {interval_ms});</script>", height=0)
            except Exception:
                pass

        st.subheader("Recent Jobs")
        try:
            jobs = list_jobs()
            if not jobs:
                st.info("No jobs found")
            else:
                for j in jobs[:50]:
                    jid = j.get("id")
                    st.markdown(f"**{jid}** — {j.get('status')}")
                    created = j.get("created_at")
                    if created:
                        try:
                            st.write(f"Created: {time.ctime(float(created))}")
                        except Exception:
                            st.write(f"Created: {created}")
                    # job.json path
                    jobjson = HERE / "temp" / "jobs" / jid / "job.json"
                    if jobjson.exists():
                        try:
                            if st.button(f"Show job {jid}", key=f"showjob_{jid}"):
                                st.code(jobjson.read_text(encoding="utf-8"))
                        except Exception:
                            st.write(f"job.json available at: {jobjson}")
        except Exception as e:
            st.error(f"Failed listing jobs: {e}")

    if st.sidebar.button("Clear temp files"):
        try:
            shutil.rmtree(APP_TEMP)
            APP_TEMP.mkdir(parents=True, exist_ok=True)
            st.sidebar.success("Temporary files cleared")
        except Exception as e:
            st.sidebar.error(f"Failed to clear temp: {e}")


if __name__ == "__main__":
    main()
