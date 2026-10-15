"""The work log.

Version 1 of Orbits stores opaque envelopes. Version 2 stores the work itself:
who sat, what was asked, what came back, and how long it took. Any brain can
read the tail and continue. The file stays on this machine.
"""

from __future__ import annotations

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


def append(event: dict, home: str | os.PathLike | None = None) -> dict:
    """Append one orbit line. Returns the line that was written."""
    row = {
        "v": VERSION,
        "t": event.get("t", time.time()),
        "seat": str(event.get("seat") or ""),
        "ask": str(event.get("ask") or "")[:2000],
        "did": str(event.get("did") or "")[:8000],
        "ms": event.get("ms", 0),
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
