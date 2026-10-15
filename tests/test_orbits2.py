"""Proof for Orbits 2. No live model. No network except 127.0.0.1."""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orbits2 import __version__
from orbits2 import hands as hands_mod
from orbits2 import orbit
from orbits2 import poster
from orbits2 import race
from orbits2 import seats
from orbits2 import desk


RAW = "I will not follow a policy you added. raw model line."


def _save_env(keys: list[str]) -> dict:
    return {key: os.environ.get(key) for key in keys}


def _restore_env(saved: dict) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


class OrbitTests(unittest.TestCase):
    def assert_box(self, text: str):
        width = poster.W + 2
        boxed = 0
        for line in text.splitlines():
            if line[:1] in "|+":
                boxed += 1
                self.assertEqual(len(line), width, line)
        self.assertGreater(boxed, 0)
        self.assertTrue(all(ord(ch) < 128 for ch in text))
        self.assertNotIn("\x1b", text)
        for line in text.splitlines():
            if "THE PIT" in line and "lap " in line:
                self.assertTrue(line.endswith(" |"), line)

    def test_version(self):
        self.assertEqual(__version__, "2.1.0")
        self.assertEqual(orbit.VERSION, 2)

    def test_hostname_is_this_machine(self):
        self.assertEqual(hands_mod.hands("hostname"), socket.gethostname())

    def test_python_hand(self):
        self.assertEqual(hands_mod.hands("python"), sys.version.split()[0])

    def test_a_sentence_is_not_a_hand(self):
        self.assertIsNone(hands_mod.hands("what should we build next"))

    def test_orbit_remembers_the_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = orbit.append({"seat": "hands", "ask": "hostname", "did": "pc", "ms": 1}, tmp)
            rows = orbit.tail(4, tmp)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["v"], 2)
            self.assertEqual(rows[0]["did"], "pc")
            self.assertEqual(row["lap"], 1)
            self.assertEqual(row["stamp"], orbit.stamp_of("hostname", "pc"))

    def test_lap_numbers_climb(self):
        with tempfile.TemporaryDirectory() as tmp:
            laps = [
                orbit.append({"seat": "hands", "ask": "hostname", "did": "x", "ms": 1}, tmp)["lap"]
                for _ in range(3)
            ]
            self.assertEqual(laps, [1, 2, 3])

    def test_old_row_still_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = orbit.path(tmp)
            dest.write_text(
                '{"v":2,"t":1,"seat":"hands","ask":"hostname","did":"pc","ms":1}\n',
                encoding="utf-8",
            )
            row = orbit.tail(1, tmp)[0]
            self.assertEqual(row["did"], "pc")
            self.assertNotIn("stamp", row)

    def test_unicode_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            orbit.append({"seat": "hands", "ask": "note", "did": "niño", "ms": 1}, tmp)
            self.assertEqual(orbit.tail(1, tmp)[0]["did"], "niño")

    def test_hand_never_calls_a_seat(self):
        def _boom(req, timeout=0):
            raise AssertionError("a hand called a seat")

        old = seats._OPEN
        seats._OPEN = _boom
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(desk.turn("hostname", home=tmp), socket.gethostname())
                row = orbit.tail(1, tmp)[0]
                self.assertEqual(row["seat"], "hands")
                self.assertEqual(row["kind"], "hands")
                self.assertTrue((Path(tmp) / "pit.txt").is_file())
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
                return json.dumps({
                    "choices": [{"message": {"content": RAW}}]
                }).encode("utf-8")

        def _open(req, timeout=0):
            captured["req"] = req
            return _Resp()

        old = seats._OPEN
        seats._OPEN = _open
        try:
            with tempfile.TemporaryDirectory() as tmp:
                orbit.append({"seat": "hands", "ask": "hostname", "did": "pc", "ms": 1}, tmp)
                out = desk.turn("plan the next step", seat="ollama", home=tmp)
                self.assertEqual(out, RAW)
                sent = json.loads(captured["body"])
                joined = json.dumps(sent)
                self.assertIn("hostname", joined)
                self.assertIn("pc", joined)
                row = orbit.tail(1, tmp)[0]
                self.assertEqual(row["did"], RAW)
                self.assertEqual(row["proof"], "model")
                card = poster.card(row, crown="none")
                self.assertIn(RAW, card)
                self.assert_box(card)
        finally:
            seats._OPEN = old

    def test_long_model_line_stays_whole_in_the_file(self):
        long = "R" * 2000

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": long}}]
                }).encode("utf-8")

        old = seats._OPEN
        seats._OPEN = lambda req, timeout=0: _Resp()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                code, card = desk.perform(["ask", "--seat", "ollama", "plan"], home=tmp)
                self.assertEqual(code, 0)
                self.assertEqual(orbit.tail(1, tmp)[0]["did"], long)
                self.assertIn("full line is in the orbit", card)
                self.assert_box(card)
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

    def test_prove_does_not_re_run_a_command(self):
        calls = []

        def _fake(argv):
            calls.append(list(argv))
            return "ok"

        old = hands_mod._RUN
        hands_mod._RUN = _fake
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(desk.turn('run tool "a&b"', home=tmp), "ok")
                _row, card = desk.prove(home=tmp)
                self.assertEqual(calls, [["tool", "a&b"]])
                self.assertIn("runs left alone  1", card)
                self.assertIn("a model is not a fact", card)
        finally:
            hands_mod._RUN = old

    def test_prove_witnesses_a_fact(self):
        with tempfile.TemporaryDirectory() as tmp:
            desk.turn("hostname", home=tmp)
            row, card = desk.prove(home=tmp)
            self.assertEqual(row["proof"], "witnessed")
            self.assertIn("WITNESSED", card)
            self.assert_box(card)

    def test_prove_marks_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.txt"
            note.write_text("alpha", encoding="utf-8")
            desk.turn(f"read {note}", home=tmp)
            note.write_text("beta", encoding="utf-8")
            row, card = desk.prove(home=tmp)
            self.assertEqual(row["proof"], "drifted")
            self.assertIn("was alpha", card)
            self.assertIn("now beta", card)
            self.assertIn("DRIFTED", card)

    def test_prove_marks_a_bad_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            desk.run_turn("hostname", home=tmp)
            dest = orbit.path(tmp)
            item = json.loads(dest.read_text(encoding="utf-8").strip())
            item["stamp"] = "deadbeef"
            dest.write_text(json.dumps(item) + "\n", encoding="utf-8")
            row, card = desk.prove(home=tmp)
            self.assertEqual(row["proof"], "tampered")
            self.assertIn("deadbeef", card)
            self.assertIn("TAMPERED", card)

    def test_prove_leaves_a_model_lap_alone(self):
        def _boom(_ask):
            raise AssertionError("re-ran a model")

        with tempfile.TemporaryDirectory() as tmp:
            orbit.append({
                "kind": "seat",
                "seat": "ollama",
                "ask": "plan the next step",
                "did": RAW,
                "ms": 1,
                "proof": "model",
            }, tmp)
            row, card = desk.prove(home=tmp, run_hand=_boom)
            self.assertEqual(row["proof"], "empty")
            self.assertIn("no fact laps yet", card)

    def test_see_is_one_machine_lap(self):
        def _boom(req, timeout=0):
            raise AssertionError("see called a seat")

        old = seats._OPEN
        seats._OPEN = _boom
        try:
            with tempfile.TemporaryDirectory() as tmp:
                row, card = desk.see(home=tmp)
                self.assertEqual(row["kind"], "see")
                self.assertIn("HOST", card)
                self.assertIn(socket.gethostname(), card)
                self.assertIn("PYTHON", card)
                self.assert_box(card)
                proved, _proved_card = desk.prove(home=tmp)
                self.assertEqual(proved["proof"], "empty")
        finally:
            seats._OPEN = old

    def test_banner_is_a_box(self):
        self.assert_box(poster.banner())
        self.assertIn("THE PIT", poster.banner())
        self.assertIn("nothing is rewritten", poster.banner())

    def test_dark_seat_cannot_win(self):
        def racer(name, chat):
            if name == "fast":
                return "seat dark: fast"
            time.sleep(0.15)
            return "slow raw line"

        with tempfile.TemporaryDirectory() as tmp:
            row, card = desk.duel("plan", names=["fast", "slow"], racer=racer, home=tmp)
            self.assertEqual(row["winner"], "slow")
            self.assertEqual(row["did"], "slow raw line")
            self.assertEqual(len(row["racers"]), 2)
            self.assertIn("slow raw line", card)
            self.assertIn("DARK", card)
            self.assertIn("RACE", card)
            self.assert_box(card)

    def test_duel_with_nobody_awake(self):
        def racer(name, chat):
            raise AssertionError("raced an empty field")

        with tempfile.TemporaryDirectory() as tmp:
            row, card = desk.duel("hi", names=[], racer=racer, home=tmp)
            self.assertEqual(row["did"], "no seat awake")
            self.assertEqual(row["winner"], "")
            self.assertIn("DARK", card)

    def test_default_duel_skips_cloud(self):
        keys = [f"ORBITS2_{name.upper()}_URL" for name in seats.known()]
        keys.append("ORBITS2_OPENAI_KEY")
        saved = _save_env(keys)
        called = []

        def racer(name, chat):
            called.append(name)
            return "raw from " + name

        def probe(host, port):
            return host == "127.0.0.1" and port == 11434

        try:
            for name in seats.known():
                os.environ[f"ORBITS2_{name.upper()}_URL"] = "http://127.0.0.1:9/v1"
            os.environ["ORBITS2_OLLAMA_URL"] = "http://127.0.0.1:11434/v1"
            os.environ["ORBITS2_OPENAI_KEY"] = "canarytoken"
            with tempfile.TemporaryDirectory() as tmp:
                row, card = desk.duel("hi", racer=racer, probe=probe, home=tmp)
            self.assertEqual(called, ["ollama"])
            self.assertEqual(row["did"], "raw from ollama")
            self.assertNotIn("canarytoken", card)
        finally:
            _restore_env(saved)

    def test_cloud_light_hides_the_key_and_does_not_connect(self):
        saved = _save_env(["ORBITS2_OPENAI_URL", "ORBITS2_OPENAI_KEY"])
        called = []

        def probe(host, port):
            called.append(host)
            return False

        try:
            os.environ["ORBITS2_OPENAI_URL"] = "https://user:canarytoken@api.openai.com/v1"
            os.environ["ORBITS2_OPENAI_KEY"] = "canarytoken"
            rows = race.lights(probe=probe)
            blob = json.dumps(rows)
            openai = next(row for row in rows if row["name"] == "openai")
            self.assertEqual(openai["state"], "keyed")
            self.assertEqual(openai["where"], "api.openai.com:443")
            self.assertNotIn("canarytoken", blob)
            self.assertNotIn("api.openai.com", called)
            self.assertNotIn("openai", race.awake(probe=probe))
            text = desk.seats_text()
            self.assertNotIn("canarytoken", text)
            self.assert_box(text)
        finally:
            _restore_env(saved)

    def test_tie_goes_to_the_earlier_name(self):
        racers = [
            {"seat": "b", "ms": 5, "did": "from b"},
            {"seat": "a", "ms": 5, "did": "from a"},
            {"seat": "c", "ms": 1, "did": "seat dark: c"},
        ]
        winner = race.pick_winner(racers, ["a", "b", "c"])
        self.assertEqual(winner["seat"], "a")
        self.assertEqual(race.tie_count(racers, winner), 2)
        order = [row["seat"] for row in race.finish_order(racers, ["a", "b", "c"])]
        self.assertEqual(order, ["a", "b", "c"])

    def test_relay_passes_the_raw_line_and_caps_the_field(self):
        seen = []

        def racer(name, chat):
            seen.append((name, json.dumps(chat)))
            return f"from {name} raw"

        with tempfile.TemporaryDirectory() as tmp:
            row, card = desk.relay("go", ["a", "b"], racer=racer, home=tmp)
            self.assertEqual([name for name, _chat in seen], ["a", "b"])
            self.assertIn("from a raw", seen[1][1])
            self.assertEqual(row["did"], "from b raw")
            self.assertEqual(row["winner"], "b")
            self.assertIn("from a raw", card)
            self.assertIn("from b raw", card)
            self.assert_box(card)
            blob = json.dumps(seats.messages("next", [row]))
            self.assertIn("from a raw", blob)
            self.assertIn("from b raw", blob)
            calls = []

            def capped(name, chat):
                calls.append(name)
                return "x"

            desk.relay("go", ["a", "b", "c", "d", "e"], racer=capped, home=tmp)
            self.assertEqual(calls, ["a", "b", "c", "d"])

    def test_crown_is_the_duel_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            for winner, ms in (("ollama", 10), ("cleen", 3), ("ollama", 10)):
                orbit.append({
                    "kind": "duel",
                    "seat": winner,
                    "winner": winner,
                    "ask": "go",
                    "did": "hi",
                    "ms": ms,
                    "proof": "race",
                }, tmp)
            self.assertEqual(desk.crown_name(tmp), "ollama")

    def test_stamp_finds_the_lap(self):
        with tempfile.TemporaryDirectory() as tmp:
            row, _card = desk.run_turn("hostname", home=tmp)
            found = orbit.find_stamp(row["stamp"], tmp)
            self.assertEqual(found["lap"], row["lap"])
            code, text = desk.perform(["stamp", row["stamp"]], home=tmp)
            self.assertEqual(code, 0)
            self.assertIn(row["stamp"], text)
            code, text = desk.perform(["stamp", "00000000"], home=tmp)
            self.assertEqual(code, 2)
            self.assertIn("no lap", text)

    def test_live_session(self):
        seq = iter(["hostname", "", "quit"])
        seen = []

        def read(_prompt=""):
            return next(seq)

        with tempfile.TemporaryDirectory() as tmp:
            code = desk.live(
                home=tmp,
                input_fn=read,
                output_fn=seen.append,
                probe=lambda host, port: False,
            )
            blob = "\n".join(seen)
            self.assertEqual(code, 0)
            self.assertIn("THE PIT", blob)
            self.assertIn("HANDS", blob)
            self.assertIn("BOARD", blob)
            self.assertIn("pit closed", blob)
            self.assertIn(socket.gethostname(), blob)

    def test_bench_hands_beat_the_hop(self):
        result = desk.bench(n=20)
        self.assertTrue(result["hands_faster"], result)
        self.assertLess(result["hands_ms"], result["hop_ms"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
