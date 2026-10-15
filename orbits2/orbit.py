"""The work log.

Version 1 of Orbits stores opaque envelopes. Version 2 stores the work itself.
A lap says who sat, what was asked, what came back, how long it took, and a
short check code of that ask and that answer. Any brain can read the tail and
continue. The file stays on this machine.

A line may also carry kind, winner, proof, and racers. Older lines omit them.
Readers use .get. The record version stays 2.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

VERSION = 2


def home_dir(home: str | os.PathLike | None = None) -> Path:
    if home:
        return Path(home)
    env = os.environ.get("ORBITS2_HOME")
    if env:
        return Path(env)
    return Path.home() / ".orbits2"


def path(home: str | os.PathLike | None = None) -> Path:
    return home_dir(home) / "orbit.jsonl"


def stamp_of(ask: str, did: str) -> str:
    """Eight hex chars over the ask and the answer. A check code, not a lock."""
    blob = (str(ask) + "\n" + str(did)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:8]


def _number(value) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _racers(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        out.append({
            "seat": str(item.get("seat") or "")[:40],
            "ms": _number(item.get("ms", 0)),
            "did": str(item.get("did") or "")[:2000],
        })
    return out


def _count(home: str | os.PathLike | None) -> int:
    dest = path(home)
    if not dest.exists():
        return 0
    return sum(1 for line in dest.read_text(encoding="utf-8").splitlines() if line.strip())


def append(event: dict, home: str | os.PathLike | None = None) -> dict:
    """Append one lap. Returns the line that was written."""
    ask = str(event.get("ask") or "")[:2000]
    did = str(event.get("did") or "")[:8000]
    seat = str(event.get("seat") or "")[:40]
    if "winner" in event:
        winner = str(event.get("winner") or "")[:40]
    else:
        winner = seat
    row = {
        "v": VERSION,
        "t": event.get("t", time.time()),
        "lap": _count(home) + 1,
        "kind": str(event.get("kind") or "seat")[:16],
        "seat": seat,
        "ask": ask,
        "did": did,
        "ms": _number(event.get("ms", 0)),
        "winner": winner,
        "proof": str(event.get("proof") or "")[:24],
        "stamp": stamp_of(ask, did),
        "racers": _racers(event.get("racers")),
    }
    dest = path(home)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def tail(n: int = 8, home: str | os.PathLike | None = None) -> list[dict]:
    dest = path(home)
    if not dest.exists():
        return []
    lines = dest.read_text(encoding="utf-8").splitlines()
    out: list[dict] = []
    for line in lines[-max(0, n):]:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def read_all(home: str | os.PathLike | None = None) -> list[dict]:
    return tail(1_000_000, home)


def find_stamp(code: str, home: str | os.PathLike | None = None) -> dict | None:
    want = (code or "").strip().lower()
    if not want:
        return None
    found = None
    for row in read_all(home):
        if str(row.get("stamp") or "").lower() == want:
            found = row
    return found
