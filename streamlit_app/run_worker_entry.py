"""
Entry script to start the job worker with imports resolved relative to `streamlit_app/`.
This ensures `from utils import ...` inside handlers resolves to `streamlit_app/utils.py`.
"""
import sys, os
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
# Prepend project root so `import streamlit_app` works, and also add streamlit_app
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, HERE)

import logging
import os
LOGS_DIR = os.path.join(HERE, "temp", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
pid_path = os.path.join(HERE, "temp", "worker.pid")
logger = logging.getLogger("worker_entry")
logger.setLevel(logging.INFO)
if not logger.handlers:
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(os.path.join(LOGS_DIR, "worker_entry.log"), maxBytes=5 * 1024 * 1024, backupCount=5)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

logger.info("Starting worker entry")

# atomic PID write helper
def _atomic_write(path: str, data: str):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        except Exception:
            logger.exception("Failed to write PID file")

try:
    _atomic_write(pid_path, str(os.getpid()))
except Exception:
    logger.exception("Failed to write PID file")

# import local modules (run from streamlit_app/ directory)
from job_worker import run_worker_loop
try:
    # start health server if available (local import)
    from health_server import start_health_server
    thread, server = start_health_server()
    logger.info("Worker health server started on port %s", os.environ.get("WORKER_HEALTH_PORT", "8001"))
except Exception:
    logger.exception("Failed to start health server")

if __name__ == '__main__':
    try:
        run_worker_loop(poll_interval=2)
    except KeyboardInterrupt:
        logging.getLogger().info("Worker entry interrupted by user")
    except Exception:
        logging.getLogger().exception("Worker entry crashed")
    finally:
        # attempt to remove pid on exit
        try:
            if os.path.exists(pid_path):
                os.remove(pid_path)
        except Exception:
            logging.getLogger().exception("Failed to remove PID file on exit")
