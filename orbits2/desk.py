"""One turn.

A hand runs in this process and the orbit records it. Anything that is not a
hand goes to the chosen seat with the recent orbit attached. The seat's text
is stored and returned as it arrived.
"""

from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import hands as hands_mod
from . import orbit
from . import seats


def turn(text: str, seat: str | None = None, home=None) -> str:
    started = time.perf_counter()
    did = hands_mod.hands(text)
    used = "hands"
    if did is None:
        used = (seat or os.environ.get("ORBITS2_SEAT") or "ollama").strip().lower()
        recent = orbit.tail(8, home)
        did = seats.ask(used, seats.messages(text, recent))
    elapsed = (time.perf_counter() - started) * 1000
    orbit.append({
        "seat": used,
        "ask": text,
        "did": did,
        "ms": round(elapsed, 2),
    }, home)
    return did


def _hop_server():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            body = b'{"choices":[{"message":{"content":"hop"}}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def bench(n: int = 40) -> dict:
    """Time in-process hands against a local HTTP hop of the same count."""
    started = time.perf_counter()
    for _ in range(n):
        hands_mod.hands("hostname")
    hands_ms = (time.perf_counter() - started) * 1000

    server = _hop_server()
    host, port = server.server_address
    old_open = seats._OPEN
    old_url = os.environ.get("ORBITS2_CLEEN_URL")
    os.environ["ORBITS2_CLEEN_URL"] = f"http://{host}:{port}/v1"

    seats._OPEN = None
    try:
        started = time.perf_counter()
        for _ in range(n):
            seats.ask("cleen", [{"role": "user", "content": "hostname"}], timeout=5)
        hop_ms = (time.perf_counter() - started) * 1000
    finally:
        seats._OPEN = old_open
        if old_url is None:
            os.environ.pop("ORBITS2_CLEEN_URL", None)
        else:
            os.environ["ORBITS2_CLEEN_URL"] = old_url
        server.shutdown()
        server.server_close()
    return {
        "n": n,
        "hands_ms": round(hands_ms, 2),
        "hop_ms": round(hop_ms, 2),
        "hands_faster": hands_ms < hop_ms,
    }
