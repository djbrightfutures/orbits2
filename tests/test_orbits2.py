"""Proof for Orbits 2. No live model. No network except 127.0.0.1."""

from __future__ import annotations

import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orbits2 import __version__
from orbits2 import hands as hands_mod
from orbits2 import seats
from orbits2.desk import bench, turn
from orbits2.orbit import append, tail


class OrbitTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "2.0.0")

    def test_hostname_is_this_machine(self):
        self.assertEqual(hands_mod.hands("hostname"), socket.gethostname())

    def test_a_sentence_is_not_a_hand(self):
        self.assertIsNone(hands_mod.hands("what should we build next"))

    def test_orbit_remembers_the_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            append({"seat": "hands", "ask": "hostname", "did": "pc", "ms": 1}, tmp)
            rows = tail(4, tmp)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["v"], 2)
            self.assertEqual(rows[0]["did"], "pc")

    def test_hand_never_calls_a_seat(self):
        def _boom(req, timeout=0):
            raise AssertionError("a hand called a seat")

        old = seats._OPEN
        seats._OPEN = _boom
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(turn("hostname", home=tmp), socket.gethostname())
                self.assertEqual(tail(1, tmp)[0]["seat"], "hands")
        finally:
            seats._OPEN = old

    def test_seat_text_is_not_rewritten(self):
        captured = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                body = captured["req"].data.decode("utf-8")
                captured["body"] = body
                raw = "I will not follow a policy you added. raw model line."
                return json.dumps({
                    "choices": [{"message": {"content": raw}}]
                }).encode("utf-8")

        def _open(req, timeout=0):
            captured["req"] = req
            return _Resp()

        old = seats._OPEN
        seats._OPEN = _open
        try:
            with tempfile.TemporaryDirectory() as tmp:
                append({"seat": "hands", "ask": "hostname", "did": "pc", "ms": 1}, tmp)
                out = turn("plan the next step", seat="ollama", home=tmp)
                self.assertEqual(out, "I will not follow a policy you added. raw model line.")
                sent = json.loads(captured["body"])
                joined = json.dumps(sent)
                self.assertIn("hostname", joined)
                self.assertIn("pc", joined)
        finally:
            seats._OPEN = old

    def test_dark_seat(self):
        def _open(req, timeout=0):
            raise OSError("down")

        old = seats._OPEN
        seats._OPEN = _open
        try:
            self.assertEqual(
                seats.ask("ollama", [{"role": "user", "content": "hi"}]),
                "seat dark: ollama",
            )
        finally:
            seats._OPEN = old

    def test_run_is_an_argument_list(self):
        seen = {}

        def _fake(argv):
            seen["argv"] = argv
            return "ok"

        old = hands_mod._RUN
        hands_mod._RUN = _fake
        try:
            out = hands_mod.hands('run tool "a&b"')
        finally:
            hands_mod._RUN = old
        self.assertEqual(out, "ok")
        self.assertEqual(seen["argv"], ["tool", "a&b"])

    def test_bench_hands_beat_the_hop(self):
        result = bench(n=20)
        self.assertTrue(result["hands_faster"], result)
        self.assertLess(result["hands_ms"], result["hop_ms"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
