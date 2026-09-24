"""platform-demo — deterministic lifecycle validation service (Phase 1).

stdlib-only HTTP service exposing:
  /health   -> 200 {"status":"ok"}     (container healthcheck target)
  /         -> 200 service metadata    (proves the app serves content)
  /ready    -> 200 after startup       (readiness probe target)

Deliberately boring: no external dependencies, no state, no secrets — the
point is a reproducible, observable container lifecycle, not features.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STARTED_AT = time.time()
READY_AFTER = float(os.environ.get("READY_AFTER_SECONDS", "1"))  # simulates startup work
VERSION = "0.1.0"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (http.server API)
        uptime = round(time.time() - STARTED_AT, 3)
        if self.path == "/health":
            self._send(200, {"status": "ok", "version": VERSION, "uptime_s": uptime})
        elif self.path == "/ready":
            if uptime >= READY_AFTER:
                self._send(200, {"status": "ready"})
            else:
                self._send(503, {"status": "starting"})
        elif self.path == "/":
            self._send(200, {
                "service": "platform-demo",
                "version": VERSION,
                "role": "phase-1 container lifecycle validation",
                "platform": "infrastructure-platform",
                "uptime_s": uptime,
            })
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # stdout logging -> docker logs
        print(f"[platform-demo] {self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"[platform-demo] v{VERSION} listening on :{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
