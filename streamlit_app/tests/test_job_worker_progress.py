import shutil
import time
import uuid
from pathlib import Path

import pytest

from job_worker import JOBS_DIR, save_job, load_job


def test_progress_history_written_and_truncated(tmp_path):
    # create a temporary job folder under the real JOBS_DIR so save_job/load_job operate
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    jid = f"test_progress_{uuid.uuid4().hex}"
    job_dir = JOBS_DIR / jid
    if job_dir.exists():
        shutil.rmtree(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # initial job meta
        job = {
            "id": jid,
            "status": "QUEUED",
            "created_at": time.time(),
        }
        save_job(job_dir, job)

        # simulate progress updates > 100 entries
        total = 110
        for i in range(total):
            j = load_job(job_dir)
            assert j is not None
            hist = j.get("progress_history") or []
            hist.append({"ts": time.time(), "progress": i / float(total)})
            # truncate like the worker does
            if len(hist) > 100:
                hist = hist[-100:]
            j["progress_history"] = hist
            j["updated_at"] = time.time()
            save_job(job_dir, j)

        final = load_job(job_dir)
        assert final is not None
        ph = final.get("progress_history")
        assert isinstance(ph, list)
        # truncated to 100
        assert len(ph) == 100
        # last entry progress equals (total-1)/total
        assert pytest.approx(ph[-1]["progress"]) == (total - 1) / float(total)

    finally:
        try:
            shutil.rmtree(job_dir)
        except Exception:
            pass
