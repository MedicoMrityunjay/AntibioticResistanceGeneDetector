import json
import time
import traceback
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from handlers import run_detection_and_collect
from job_manager import load_job, save_job

JOBS_DIR = Path(__file__).parent / "temp" / "jobs"

# Worker defaults
DEFAULT_POLL_INTERVAL = 2
RETENTION_HOURS = 48
MAX_ATTEMPTS = 2

# Retention policy (configurable)
MAX_COMPLETED_JOBS = 50
MAX_JOB_AGE_DAYS = 7
# How often to run cleanup (seconds)
CLEANUP_INTERVAL = 300

# Log retention
LOG_RETENTION_DAYS = 7

# Logging and heartbeat
LOGS_DIR = Path(__file__).parent / "temp" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_FILE = Path(__file__).parent / "temp" / "worker.heartbeat.json"
PID_FILE = Path(__file__).parent / "temp" / "worker.pid"


def _setup_logger():
    logger = logging.getLogger("streamlit_job_worker")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = RotatingFileHandler(LOGS_DIR / "worker.log", maxBytes=5 * 1024 * 1024, backupCount=5)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


LOGGER = _setup_logger()


def _atomic_write(path: Path, data: str, encoding: str = "utf-8"):
    tmp = path.with_suffix(path.suffix + ".tmp")
    # write to tmp then replace (os.replace is atomic on most OSes)
    tmp.write_text(data, encoding=encoding)
    try:
        os.replace(str(tmp), str(path))
    except Exception:
        # best-effort fallback
        path.write_text(data, encoding=encoding)


def _prune_logs(older_than_days: int = LOG_RETENTION_DAYS):
    try:
        cutoff = time.time() - (older_than_days * 86400)
        for p in LOGS_DIR.iterdir():
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink()
            except Exception:
                continue
    except Exception:
        LOGGER.exception("Log pruning failed")


def _cleanup_jobs(max_jobs: int = MAX_COMPLETED_JOBS, max_age_days: int = MAX_JOB_AGE_DAYS):
    """Remove old COMPLETED/FAILED job folders while keeping the most recent `max_jobs`.

    Never touch RUNNING jobs. Also delete jobs older than `max_age_days` days.
    """
    try:
        jobs = []
        for jd in JOBS_DIR.iterdir():
            if not jd.is_dir():
                continue
            meta = load_job(jd.name)
            if not meta:
                continue
            status = meta.get("status")
            if status in ("COMPLETED", "FAILED"):
                created = meta.get("created_at", 0)
                jobs.append((jd, created, meta))

        # sort newest first
        jobs_sorted = sorted(jobs, key=lambda x: x[1] or 0, reverse=True)

        # Delete by age first
        cutoff = time.time() - (max_age_days * 86400)
        for jd, created, meta in list(jobs_sorted):
            if created and created < cutoff:
                try:
                    # safe delete
                    for p in sorted(jd.rglob("*"), reverse=True):
                        try:
                            if p.is_file():
                                p.unlink()
                            else:
                                p.rmdir()
                        except Exception:
                            pass
                    jd.rmdir()
                    LOGGER.info("Deleted job by age: %s", str(jd))
                except Exception:
                    LOGGER.exception("Failed deleting old job %s", str(jd))

        # Refresh list and enforce max_jobs
        jobs = []
        for jd in JOBS_DIR.iterdir():
            if not jd.is_dir():
                continue
            meta = load_job(jd.name)
            if not meta:
                continue
            if meta.get("status") in ("COMPLETED", "FAILED"):
                jobs.append((jd, meta.get("created_at", 0)))

        jobs_sorted = sorted(jobs, key=lambda x: x[1] or 0, reverse=True)
        # keep first max_jobs, delete the rest
        for to_delete in jobs_sorted[max_jobs:]:
            jd = to_delete[0]
            try:
                for p in sorted(jd.rglob("*"), reverse=True):
                    try:
                        if p.is_file():
                            p.unlink()
                        else:
                            p.rmdir()
                    except Exception:
                        pass
                jd.rmdir()
                LOGGER.info("Pruned old job to respect max_jobs: %s", str(jd))
            except Exception:
                LOGGER.exception("Failed pruning job %s", str(jd))

        # prune logs too
        _prune_logs()
    except Exception:
        LOGGER.exception("Job cleanup failed")


# job_manager provides load_job/save_job; _atomic_write retained for heartbeat and pid


def run_worker_loop(poll_interval=2):
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    # write pid file (atomic)
    try:
        _atomic_write(PID_FILE, str(os.getpid()))
    except Exception:
        LOGGER.exception("Failed to write PID file")

    start_time = time.time()
    last_job_id = None
    last_job_attempts = 0
    last_error = None

    # Recover any jobs left in RUNNING state (from prior crashes) by re-queuing them
    for jd in JOBS_DIR.iterdir():
        if not jd.is_dir():
            continue
        try:
            meta = load_job(jd.name)
        except Exception:
            meta = None
        if not meta:
            continue
        if meta.get("status") == "RUNNING":
            meta["status"] = "QUEUED"
            meta["updated_at"] = time.time()
            save_job(jd, meta)

    last_cleanup = time.time()

    try:
        while True:
            for job_dir in JOBS_DIR.iterdir():
                if not job_dir.is_dir():
                    continue

                try:
                    job = load_job(job_dir.name)
                except Exception:
                    job = None
                if not job:
                    continue

                status = job.get("status")
                if status == "CANCELLED":
                    # skip cancelled jobs
                    continue

                if status != "QUEUED":
                    # Skip anything not queued
                    continue

                # Implement a simple lock to avoid double-processing
                lock_file = job_dir / ".lock"
                if lock_file.exists():
                    # already being processed by another worker/process
                    continue
                try:
                    lock_file.write_text(str(time.time()))
                except Exception:
                    # could not create lock; skip this job for now
                    continue

                # bump attempt counter
                job["attempts"] = int(job.get("attempts", 0)) + 1
                job["status"] = "RUNNING"
                job["updated_at"] = time.time()
                save_job(job_dir, job)

                def progress_hook(p):
                    nonlocal last_job_id, last_job_attempts, last_error
                    try:
                        if not isinstance(job, dict):
                            return
                        job.setdefault("progress_history", []).append({"ts": time.time(), "progress": p})
                        # keep last N entries small to avoid uncontrolled growth
                        if len(job["progress_history"]) > 100:
                            job["progress_history"] = job["progress_history"][-100:]
                        job["updated_at"] = time.time()
                        save_job(job_dir, job)
                        # record last active job for heartbeat
                        last_job_id = job.get("id")
                        last_job_attempts = int(job.get("attempts", 0))
                    except Exception:
                        try:
                            jid = job.get("id") if isinstance(job, dict) else "<unknown>"
                            LOGGER.exception("Failed to write progress for job %s", jid)
                        except Exception:
                            pass

                try:
                    params = job.get("params") or job.get("parameters") or {}
                    res = run_detection_and_collect(
                        uploaded_files=None,
                        fasta_dir=str(job_dir / "input"),
                        db_path=params.get("db_path") or job.get("db_path"),
                        gene_map=params.get("gene_map") or job.get("gene_map"),
                        identity=float(params.get("identity", job.get("identity", 0.0))),
                        coverage=int(params.get("coverage", job.get("coverage", 0))),
                        threads=int(params.get("threads", job.get("threads", 1))),
                        outdir=str(job_dir / "output"),
                        temp_dir=job_dir,
                        plot=bool(params.get("plot", job.get("plot", False))),
                        summary=bool(params.get("summary", job.get("summary", False))),
                        quiet=True,
                        rich=False,
                        progress_callback=progress_hook,
                        mock_mode=bool(job.get("mock_mode", False)),
                    )

                    # Successful run
                    job["status"] = "COMPLETED"
                    job["message"] = res.get("message", "Run completed") if isinstance(res, dict) else "Run completed"
                    # Prefer csv_bytes -> write a local file and record path
                    results = {}
                    try:
                        out_folder = job_dir / "output"
                        out_folder.mkdir(parents=True, exist_ok=True)
                        csv_bytes = None
                        if isinstance(res, dict):
                            csv_bytes = res.get("csv_bytes")
                        if isinstance(csv_bytes, str):
                            csv_bytes = csv_bytes.encode("utf-8")
                        if isinstance(csv_bytes, (bytes, bytearray)):
                            csv_path = out_folder / "results.csv"
                            csv_path.write_bytes(csv_bytes)
                            results["csv"] = str(csv_path)

                        plots_zip = None
                        if isinstance(res, dict):
                            plots_zip = res.get("plots_zip")
                        if isinstance(plots_zip, str):
                            plots_zip = plots_zip.encode("utf-8")
                        if isinstance(plots_zip, (bytes, bytearray)):
                            plots_path = out_folder / "plots.zip"
                            plots_path.write_bytes(plots_zip)
                            results["plots"] = str(plots_path)
                    except Exception as e:
                        # saving artifacts failed; still mark job completed but note error
                        job.setdefault("worker_notes", "")
                        job["worker_notes"] += f"\nArtifact save error: {e}"

                    job["output_files"] = list(results.values())
                    job["updated_at"] = time.time()
                    save_job(job_dir, job)
                    LOGGER.info("Job %s artifacts written: %s", job.get("id"), json.dumps(results))
                except Exception as exc:
                    tb = traceback.format_exc()
                    last_error = tb
                    # if we have remaining attempts, requeue, else mark failed
                    attempts = int(job.get("attempts", 0))
                    if attempts < MAX_ATTEMPTS:
                        job["status"] = "QUEUED"
                        job["last_error"] = tb
                        job["message"] = str(exc)
                        job.setdefault("worker_notes", "")
                        job["worker_notes"] = job.get("worker_notes", "") + f"\nRetrying after error: {str(exc)}"
                        job["updated_at"] = time.time()
                    else:
                        job["status"] = "FAILED"
                        job["last_error"] = tb
                        job["message"] = str(exc)
                        job["updated_at"] = time.time()
                    save_job(job_dir, job)
                    LOGGER.exception("Job %s failed on attempt %s", job.get("id"), attempts)
                finally:
                    # remove lock when done or on error
                    try:
                        if lock_file.exists():
                            lock_file.unlink()
                    except Exception:
                        pass

                # Heartbeat (health-check): write JSON with basic status so external monitors can see worker is alive
                try:
                    hb = {
                        "ts": time.time(),
                        "pid": int(os.getpid()),
                        "uptime": time.time() - start_time,
                        "status": "RUNNING",
                        "last_job_id": last_job_id,
                        "last_job_attempts": last_job_attempts,
                        "last_error": last_error,
                    }
                    _atomic_write(HEARTBEAT_FILE, json.dumps(hb))
                except Exception:
                    try:
                        LOGGER.exception("Failed writing heartbeat file")
                    except Exception:
                        pass

                # periodic cleanup
                try:
                    if time.time() - last_cleanup > CLEANUP_INTERVAL:
                        _cleanup_jobs()
                        last_cleanup = time.time()
                except Exception:
                    LOGGER.exception("Cleanup scheduling failed")

            # Retention cleanup: remove old completed/failed job folders
            try:
                cutoff = time.time() - (RETENTION_HOURS * 3600)
                for jd in JOBS_DIR.iterdir():
                    if not jd.is_dir():
                        continue
                    try:
                        meta = load_job(jd.name)
                    except Exception:
                        meta = None
                    if not meta:
                        continue
                    status = meta.get("status")
                    if status in ("COMPLETED", "FAILED", "CANCELLED"):
                        created = meta.get("created_at", 0)
                        if created and created < cutoff:
                            # delete
                            try:
                                # recursive delete
                                for p in sorted(jd.rglob("*"), reverse=True):
                                    try:
                                        if p.is_file():
                                            p.unlink()
                                        else:
                                            p.rmdir()
                                    except Exception:
                                        pass
                                jd.rmdir()
                            except Exception:
                                pass
            except Exception:
                pass

            time.sleep(poll_interval)
    finally:
        # cleanup pid and heartbeat on exit
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except Exception:
            LOGGER.exception("Failed to remove PID file on exit")
        try:
            if HEARTBEAT_FILE.exists():
                HEARTBEAT_FILE.unlink()
        except Exception:
            LOGGER.exception("Failed to remove heartbeat file on exit")
