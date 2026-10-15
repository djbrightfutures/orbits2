"""The pit.

A fact runs in this process and becomes a lap. Anything else goes to a seat.
A duel races awake local seats. A named cloud seat is called only when you
name it. Prove re-runs facts. Model text is stored as it arrived.
"""

from __future__ import annotations

import os
import shlex
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from . import hands as hands_mod
from . import orbit
from . import poster
from . import race
from . import seats
from . import witness

COMMANDS = """
pit      the card you photograph
live     stay in the pit
see      this machine, one lap
prove    re-run facts and mark drift
duel     race the awake local seats
relay    pass one ask through named seats
board    last laps, the crown, the lights
stamp    find a lap by its check code
bench    hands against a local hop
seats    where each brain points
tail     the last lines of the orbit
version  the program version

duel --seats ollama,cleen <ask>
relay --seats ollama,cleen <ask>
ask --seat ollama <ask>
hands hostname

a fact stays in this process: hostname, whoami, cwd, disk, python, list, read, run.
run is an argument list, never a shell.
anything else goes to a seat. the seat's text is kept as it arrived.
a cloud seat is raced only when you name it.
""".strip("\n")


def help_text() -> str:
    return poster.banner() + "\n" + COMMANDS + "\n" + __version__ + "\n"


def crown_name(home=None) -> str:
    wins: dict[str, int] = {}
    times: dict[str, list[float]] = {}
    for row in orbit.read_all(home):
        if row.get("kind") != "duel":
            continue
        winner = str(row.get("winner") or "")
        if not winner:
            continue
        wins[winner] = wins.get(winner, 0) + 1
        try:
            times.setdefault(winner, []).append(float(row.get("ms") or 0))
        except (TypeError, ValueError):
            times.setdefault(winner, []).append(0.0)
    if not wins:
        return "none"
    best = max(wins.values())
    names = [name for name, count in wins.items() if count == best]

    def average(name: str) -> float:
        vals = times.get(name) or [0.0]
        return sum(vals) / len(vals)

    names.sort(key=lambda name: (average(name), name))
    return names[0]


def record(event: dict, home=None) -> tuple[dict, str]:
    row = orbit.append(event, home)
    text = poster.card(row, crown=crown_name(home))
    try:
        dest = orbit.home_dir(home) / "pit.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text + "\n", encoding="utf-8", newline="\n")
    except OSError:
        pass
    return row, text


def run_turn(text: str, seat: str | None = None, home=None) -> tuple[dict, str]:
    started = time.perf_counter()
    did = hands_mod.hands(text)
    if did is None:
        used = (seat or os.environ.get("ORBITS2_SEAT") or "ollama").strip().lower()
        recent = orbit.tail(8, home)
        did = seats.ask(used, seats.messages(text, recent))
        kind = "seat"
        proof = "model"
    else:
        used = "hands"
        kind = "hands"
        proof = "unchecked"
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    return record({
        "kind": kind,
        "seat": used,
        "ask": text,
        "did": did,
        "ms": elapsed,
        "winner": used,
        "proof": proof,
        "racers": [{"seat": used, "ms": elapsed, "did": did}],
    }, home)


def turn(text: str, seat: str | None = None, home=None) -> str:
    row, _card = run_turn(text, seat=seat, home=home)
    return row["did"]


def see(home=None) -> tuple[dict, str]:
    started = time.perf_counter()
    clock = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())
    did = "\n".join([
        f"HOST     {hands_mod.hands('hostname') or ''}",
        f"USER     {hands_mod.hands('whoami') or ''}",
        f"CWD      {hands_mod.hands('cwd') or ''}",
        f"DISK     {hands_mod.hands('disk') or ''}",
        f"PYTHON   {hands_mod.hands('python') or ''}",
        f"CLOCK    {clock}",
    ])
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    return record({
        "kind": "see",
        "seat": "hands",
        "ask": "see",
        "did": did,
        "ms": elapsed,
        "winner": "hands",
        "proof": "machine",
    }, home)


def prove(home=None, run_hand=None) -> tuple[dict, str]:
    started = time.perf_counter()
    judged = witness.judge(orbit.read_all(home), run_hand or hands_mod.hands)
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    return record({
        "kind": "prove",
        "seat": "hands",
        "ask": "prove",
        "did": judged["did"],
        "ms": elapsed,
        "winner": "hands",
        "proof": judged["proof"],
    }, home)


def _default_racer(timeout: float):
    def racer(name: str, chat: list) -> str:
        return seats.ask(name, chat, timeout=timeout)
    return racer


def duel(text: str, names: list[str] | None = None, home=None, racer=None, probe=None, timeout: float = 8.0):
    order = list(names) if names is not None else race.awake(probe)
    runner = racer or _default_racer(timeout)
    recent = orbit.tail(8, home)
    event = race.duel_field(text, order, runner, recent, timeout=timeout)
    return record(event, home)


def relay(text: str, names: list[str] | None, home=None, racer=None, timeout: float = 8.0):
    runner = racer or _default_racer(timeout)
    recent = orbit.tail(8, home)
    event = race.relay_field(text, list(names or []), runner, recent)
    return record(event, home)


def show_board(home=None, probe=None) -> str:
    return poster.board(orbit.read_all(home), race.lights(probe), crown_name(home))


def seats_text() -> str:
    lines = []
    for name in seats.known():
        url = seats.url_for(name)
        where = race.public_where(url)
        if not url:
            state = "no url"
        elif race.is_local(url):
            state = "local"
        elif seats.key_for(name):
            state = "key"
        else:
            state = "no key"
        lines.append(f"{name:<10} {state:<6} {where:<22} {seats.model_for(name)}")
    return poster.panel("SEATS", lines)


def pit(home=None, probe=None) -> str:
    _row, seen = see(home)
    return "\n".join([poster.banner(), seen, show_board(home, probe=probe)])


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


def bench_card(result: dict | None = None) -> str:
    result = bench() if result is None else result
    faster = "hands beat the hop" if result["hands_faster"] else "the hop was faster"
    text = poster.panel("BENCH", [
        f"hands   {result['hands_ms']:.2f} ms",
        f"hop     {result['hop_ms']:.2f} ms",
        f"n       {result['n']}",
        faster,
    ])
    return text


def _flags(argv: list[str]) -> tuple[str | None, list[str] | None, str, str | None]:
    seat = None
    names = None
    rest = list(argv)
    error = None
    while rest and rest[0] in ("--seat", "--seats"):
        flag = rest[0]
        if len(rest) < 2:
            return None, None, "", f"{flag} needs a value"
        if flag == "--seat":
            seat = rest[1].strip().lower()
        else:
            names = [part.strip().lower() for part in rest[1].split(",") if part.strip()]
        rest = rest[2:]
    return seat, names, " ".join(rest).strip(), error


def perform(args: list[str], home=None, probe=None) -> tuple[int, str]:
    if not args or args[0] in ("-h", "--help", "help"):
        return 0, help_text()
    cmd = args[0]
    if cmd == "version":
        return 0, __version__ + "\nTHE PIT\n"
    if cmd == "live":
        return 2, "already in the pit\n"
    if cmd == "bench":
        result = bench()
        code = 0 if result["hands_faster"] else 1
        return code, bench_card(result)
    if cmd == "seats":
        return 0, seats_text()
    if cmd == "tail":
        rows = orbit.read_all(home)[-8:]
        if not rows:
            return 0, "orbit is empty\n"
        crown = crown_name(home)
        return 0, "\n".join(poster.card(row, crown=crown) for row in rows)
    if cmd == "board":
        return 0, show_board(home, probe=probe)
    if cmd == "pit":
        return 0, pit(home, probe=probe)
    if cmd == "see":
        _row, text = see(home)
        return 0, text
    if cmd == "prove":
        _row, text = prove(home)
        return 0, text
    if cmd == "stamp":
        code = " ".join(args[1:]).strip()
        if not code:
            return 2, "stamp needs the check code\n"
        found = orbit.find_stamp(code, home)
        if not found:
            return 2, "no lap carries that code\n"
        return 0, poster.card(found, crown=crown_name(home))
    if cmd == "hands":
        text = " ".join(args[1:]).strip()
        out = hands_mod.hands(text)
        if out is None:
            return 2, "not a hand\n"
        return 0, out + "\n"
    if cmd in ("duel", "relay", "ask"):
        seat, names, text, error = _flags(args[1:])
        if error:
            return 2, error + "\n"
        if not text:
            return 2, f"{cmd} needs an ask\n"
        if cmd == "ask":
            _row, card = run_turn(text, seat=seat, home=home)
            return 0, card
        if cmd == "relay" and not names:
            return 2, "relay needs --seats a,b and an ask\n"
        if cmd == "duel":
            _row, card = duel(text, names=names, home=home, probe=probe)
            return 0, card
        _row, card = relay(text, names=names, home=home)
        return 0, card
    _row, card = run_turn(" ".join(args), home=home)
    return 0, card


def live(home=None, input_fn=None, output_fn=None, probe=None) -> int:
    read = input_fn or input
    write = output_fn or (lambda text: print(text, end="" if text.endswith("\n") else "\n"))
    write(poster.banner())
    write("type help, or a line. an empty line shows the board. quit leaves.")
    while True:
        try:
            line = read("pit> ")
        except (EOFError, KeyboardInterrupt):
            write("pit closed")
            return 0
        if line is None:
            write("pit closed")
            return 0
        text = str(line).strip()
        if text in ("quit", "exit"):
            write("pit closed")
            return 0
        if not text:
            write(show_board(home, probe=probe))
            continue
        if text == "live":
            write("already in the pit")
            continue
        try:
            argv = shlex.split(text, posix=True)
        except ValueError:
            argv = [text]
        _code, shown = perform(argv, home=home, probe=probe)
        if shown:
            write(shown)
    return 0


def emit(text: str) -> None:
    if not text:
        return
    shown = text
    use_color = (
        sys.stdout.isatty()
        and not os.environ.get("NO_COLOR")
        and os.environ.get("ORBITS2_COLOR", "1") != "0"
    )
    if use_color:
        shown = poster.tint(text)
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    data = (shown if shown.endswith("\n") else shown + "\n").encode(enc, "replace")
    buf = getattr(sys.stdout, "buffer", None)
    if buf is None:
        print(shown)
        return
    buf.write(data)
    buf.flush()
