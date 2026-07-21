#!/usr/bin/env python3
"""Reyse Ops Console — tiny local bridge between voice-line's signal bus and
the fullscreen visualizer page. Standard library only, read-only on the bus."""

import json
import math
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8777
MOCK_PORT = 8778

# Paths to voice-line's signal bus files — kept as constants so a different
# install location only needs changing here.
VOICE_LINE_DIR = os.path.expanduser("~/voice-line")
STATE_FILE = os.path.join(VOICE_LINE_DIR, ".voice_state")
WAVEFORM_FILE = os.path.join(VOICE_LINE_DIR, ".voice_waveform")
ALERT_FILE = os.path.join(VOICE_LINE_DIR, ".voice_alert")

WAVEFORM_FRESH_SECONDS = 2.0
LEVEL_SCALE = 4.0  # tune if speech reads too quiet/loud on screen

VALID_STATES = ("idle", "listening", "thinking", "speaking")

MOCK = "--mock" in sys.argv
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

# Mock script: (state, duration_seconds). "alert" fires as a flag over idle,
# same as it would for real (alert is independent of the state enum).
MOCK_SCRIPT = [
    ("idle", 3.0, False),
    ("listening", 2.0, False),
    ("thinking", 2.0, False),
    ("speaking", 4.0, False),
    ("idle", 2.0, True),
]
MOCK_TOTAL = sum(seg[1] for seg in MOCK_SCRIPT)
MOCK_START = time.time()


def read_real_state():
    state = "idle"
    level = 0.0
    alert = os.path.exists(ALERT_FILE)

    try:
        with open(STATE_FILE, "r") as f:
            s = f.read().strip()
            if s in VALID_STATES:
                state = s
    except OSError:
        pass

    waveform_fresh = False
    try:
        with open(WAVEFORM_FILE, "r") as f:
            data = json.load(f)
        ts = float(data.get("ts", 0))
        samples = data.get("samples") or []
        if samples and (time.time() - ts) <= WAVEFORM_FRESH_SECONDS:
            waveform_fresh = True
            mean_abs = sum(abs(float(x)) for x in samples) / len(samples)
            level = max(0.0, min(1.0, mean_abs * LEVEL_SCALE))
    except (OSError, ValueError, TypeError):
        pass

    # Stomp-tolerance: a live waveform means the voice is speaking no matter
    # what the state file says, so a stray process can't freeze the show.
    if waveform_fresh:
        state = "speaking"

    return {"state": state, "level": round(level, 3), "alert": alert}


def read_mock_state():
    elapsed = (time.time() - MOCK_START) % MOCK_TOTAL
    acc = 0.0
    for state, duration, alert in MOCK_SCRIPT:
        if elapsed < acc + duration:
            progress = elapsed - acc
            level = 0.0
            if state == "speaking":
                level = max(0.0, math.sin(progress * 2.4)) * 0.8 + 0.15
            return {"state": state, "level": round(level, 3), "alert": alert}
        acc += duration
    return {"state": "idle", "level": 0.0, "alert": False}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep stdout quiet; errors still raise normally

    def _send_json(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath, content_type):
        try:
            with open(filepath, "rb") as f:
                body = f.read()
        except OSError:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Strip the query string before matching — a raw self.path match on
        # "/" misses requests like "/?shot=speaking&t=1200" entirely.
        path = urlparse(self.path).path

        if path == "/state":
            data = read_mock_state() if MOCK else read_real_state()
            self._send_json(data)
            return

        if path in ("/", "/index.html"):
            self._send_file(INDEX_PATH, "text/html; charset=utf-8")
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = MOCK_PORT if MOCK else PORT
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((HOST, port), Handler)
    mode = "mock" if MOCK else "live"
    print(f"Reyse Ops Console server running at http://{HOST}:{port} ({mode})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
