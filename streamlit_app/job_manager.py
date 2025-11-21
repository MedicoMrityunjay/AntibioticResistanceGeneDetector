"""
Simple job manager using the filesystem for persistence.

Jobs are stored under `temp/jobs/<job_id>/` with a `job.json` metadata file.
This module provides simple CRUD style helpers used by the Streamlit UI.
"""
from pathlib import Path
import json
import uuid
import time
import os
from typing import Dict, Any, List


JOBS_ROOT = Path(__file__).resolve().parent / "temp" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)


def _job_dir(job_id: str) -> Path:
    return JOBS_ROOT / job_id


def create_job(uploaded_files: List[Dict[str, Any]], parameters: Dict[str, Any]) -> str:
    """Create a new job entry and persist inputs metadata.

    uploaded_files: a list of dicts with keys: name and written_path (optional)
    parameters: arbitrary dict of user-supplied params
    Returns job_id
    """
    try:
        job_id = uuid.uuid4().hex
        jd = _job_dir(job_id)
        jd.mkdir(parents=True, exist_ok=True)
        now = time.time()
        meta = {
            "id": job_id,
            "status": "QUEUED",
            "created_at": now,
            "updated_at": now,
            "attempts": 0,
            "progress_history": [],
            "last_error": None,
            "mock_mode": bool(parameters.get("mock_mode", False)) if isinstance(parameters, dict) else False,
            "params": parameters or {},
            "input_files": [f.get("name") for f in (uploaded_files or [])],
            "output_files": [],
            "worker_notes": "",
            "message": "",
        }
        # atomic write
        jf = jd / "job.json"
        tmp = jf.with_suffix(jf.suffix + ".tmp")
        tmp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        try:
            os.replace(str(tmp), str(jf))
        except Exception:
            jf.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return job_id
    except Exception as exc:
        tb = None
        try:
            import traceback

            tb = traceback.format_exc()
        except Exception:
            tb = str(exc)
        return {
            "status": "FAILED",
            "message": "Failed creating job",
            "logs": tb or "",
            "results_object": [],
            "fallback_to_mock": False,
            "last_error": tb,
        }


def load_job(job_id: str) -> Dict[str, Any]:
    jd = _job_dir(job_id)
    jf = jd / "job.json"
    if not jf.exists():
        raise FileNotFoundError(f"Job not found: {job_id}")
    return json.loads(jf.read_text(encoding="utf-8"))


def save_job(job_id_or_path, data: Dict[str, Any]) -> None:
    """Atomically save a job dict to its job.json. Accepts job_id or Path."""
    try:
        if isinstance(job_id_or_path, (str,)):
            jd = _job_dir(job_id_or_path)
        else:
            jd = Path(job_id_or_path)
        jf = jd / "job.json"
        tmp = jf.with_suffix(jf.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.replace(str(tmp), str(jf))
        except Exception:
            jf.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        # Best-effort: do not raise from save
        pass


def update_job(job_id: str, **kwargs) -> Dict[str, Any]:
    """Update a job with arbitrary fields. Always sets `updated_at`.

    Returns the updated job dict, or a failure-shaped dict on error.
    """
    try:
        job = load_job(job_id)
    except Exception as exc:
        tb = None
        try:
            import traceback

            tb = traceback.format_exc()
        except Exception:
            tb = str(exc)
        return {
            "status": "FAILED",
            "message": f"Job not found: {job_id}",
            "logs": tb or "",
            "results_object": [],
            "fallback_to_mock": False,
            "last_error": tb,
        }

    # apply updates
    for k, v in kwargs.items():
        if k == "progress":
            job.setdefault("progress_history", []).append({"ts": time.time(), "progress": v})
        elif k == "result_files":
            job.setdefault("output_files", []).append(v)
        else:
            job[k] = v

    job["updated_at"] = time.time()
    # ensure attempts numeric
    job["attempts"] = int(job.get("attempts", 0))

    try:
        save_job(job_id, job)
    except Exception:
        pass
    return job


def list_jobs() -> List[Dict[str, Any]]:
    out = []
    for jd in sorted(JOBS_ROOT.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        jf = jd / "job.json"
        if jf.exists():
            try:
                out.append(json.loads(jf.read_text(encoding="utf-8")))
            except Exception:
                continue
    return out
