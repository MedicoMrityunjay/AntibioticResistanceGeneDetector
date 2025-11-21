"""Small HTTP server to expose worker heartbeat JSON for monitoring.

Provides `/health` which returns the contents of the heartbeat file as JSON
or a minimal JSON object if the file is missing. Runs in a background thread.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import os
import json
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
HEARTBEAT_FILE = HERE / "temp" / "worker.heartbeat.json"
LOGS_DIR = HERE / "temp" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# setup logger for health server
import logging
from logging.handlers import RotatingFileHandler
_hs_logger = logging.getLogger("health_server")
if not _hs_logger.handlers:
    fh = RotatingFileHandler(LOGS_DIR / "health_server.log", maxBytes=5 * 1024 * 1024, backupCount=5)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    _hs_logger.setLevel(logging.INFO)
    _hs_logger.addHandler(fh)


class HealthHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path not in ("/health", "/health/"):
            self.send_response(404)
            self.end_headers()
            return

        hb = None
        try:
            if HEARTBEAT_FILE.exists():
                txt = HEARTBEAT_FILE.read_text(encoding="utf-8")
                hb = json.loads(txt)
        except Exception:
            hb = None

        if hb is None:
            # return fallback
            hb = {
                "ts": None,
                "pid": None,
                "uptime": None,
                "last_job_id": None,
                "status": "unknown",
            }
            self._send_json(hb, status=503)
            return

        self._send_json(hb, status=200)


def start_health_server(port: Optional[int] = None):
    """Start the health HTTP server in a daemon thread. Returns the Thread object.

    Port is taken from `WORKER_HEALTH_PORT` env var if not provided; default 8001.
    """
    if port is None:
        try:
            port = int(os.environ.get("WORKER_HEALTH_PORT", "8001"))
        except Exception:
            port = 8001

    server = ThreadingHTTPServer(("127.0.0.1", port), HealthHandler)

    thread = threading.Thread(target=server.serve_forever, name="worker-health-server", daemon=True)
    thread.start()
    try:
        _hs_logger.info("Health server started on http://127.0.0.1:%s/health", port)
    except Exception:
        pass
    return thread, server
