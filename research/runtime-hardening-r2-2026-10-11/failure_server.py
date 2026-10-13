"""Local development fault harness; no training or final-test scoring.

The first two example-prediction requests are held until their local gate files
appear, then fail with an explicit synthetic HTTP error. A later case load can
also be held. All other routes use the ordinary application handler. No input
values are stored; event records contain only test stages and public case IDs.
"""
from pathlib import Path
import json
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import server

CONTROL = Path(__file__).resolve().parent / "control"
CONTROL.mkdir(exist_ok=True)
LOCK = threading.Lock()
counter = 0


def wait_gate(name):
    (CONTROL / (name + ".started.json")).write_text(json.dumps({"stage": name}))
    until = time.monotonic() + 60
    while not (CONTROL / (name + ".release")).exists() and time.monotonic() < until:
        time.sleep(.05)


class FaultHandler(server.Handler):
    def do_POST(self):
        global counter
        if self.path == "/api/predict":
            with LOCK:
                counter += 1
                selected = counter
            if selected <= 2:
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                wait_gate("prediction-" + str(selected))
                self.reply({"error": "Synthetic delayed prediction failure " + str(selected)}, 503)
                return
        super().do_POST()

    def do_GET(self):
        if self.path.startswith("/api/cases/UCI411-050?") and (CONTROL / "hold-case-050").exists():
            wait_gate("case-050")
        super().do_GET()


if __name__ == "__main__":
    print(json.dumps({"url": "http://127.0.0.1:8811/", "purpose": "synthetic delayed-failure browser test"}), flush=True)
    server.ThreadingHTTPServer(("127.0.0.1", 8811), FaultHandler).serve_forever()
