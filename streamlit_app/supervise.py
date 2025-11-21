"""Simple supervisor for the worker process.

Monitors `temp/worker.heartbeat.json` and restarts the worker entry if the
heartbeat is stale or the worker process dies. Runs on Windows and uses
subprocess to start `run_worker_entry.py` from the `streamlit_app` folder.

Usage: python supervise.py
"""
import subprocess
import time
import os
import json
from pathlib import Path

HERE = Path(__file__).parent
HEARTBEAT = HERE / "temp" / "worker.heartbeat.json"
ENTRY = HERE / "run_worker_entry.py"

CHECK_INTERVAL = 5
STALE_SECONDS = 30


def start_worker():
    # Start the worker as a detached process
    popen = subprocess.Popen(["python", str(ENTRY)], cwd=str(HERE))
    return popen


def read_hb():
    try:
        if not HEARTBEAT.exists():
            return None
        txt = HEARTBEAT.read_text(encoding="utf-8")
        return json.loads(txt)
    except Exception:
        return None


def supervise_loop():
    proc = start_worker()
    print(f"Supervisor: started worker pid={proc.pid}")
    try:
        while True:
            hb = read_hb()
            now = time.time()
            stale = False
            if hb and hb.get("ts"):
                try:
                    ts = float(hb.get("ts"))
                    if now - ts > STALE_SECONDS:
                        stale = True
                except Exception:
                    stale = True
            else:
                stale = True

            # restart if process died or heartbeat stale
            if proc.poll() is not None:
                print("Supervisor: worker process exited; restarting")
                proc = start_worker()
                print(f"Supervisor: restarted worker pid={proc.pid}")
            elif stale:
                print("Supervisor: heartbeat stale; restarting worker")
                try:
                    proc.kill()
                except Exception:
                    pass
                proc = start_worker()
                print(f"Supervisor: restarted worker pid={proc.pid}")

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Supervisor: exiting, stopping worker")
        try:
            proc.kill()
        except Exception:
            pass


if __name__ == '__main__':
    supervise_loop()
