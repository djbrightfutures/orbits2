"""Prove the laps that were facts.

A hands lap is re-run. The same answer is witnessed. A different answer
drifted. A run is an action, so it is left alone. A model lap is not a fact,
so it is not re-run. A check code that no longer matches the line was edited.
"""

from __future__ import annotations

from .orbit import stamp_of

_PURE = ("hostname", "whoami", "cwd", "disk", "python")


def pure_ask(ask: str) -> bool:
    raw = (ask or "").strip()
    cmd, _, rest = raw.partition(" ")
    cmd = cmd.lower()
    if cmd in _PURE and not rest:
        return True
    if cmd in ("list", "read") and bool(rest.strip()):
        return True
    return False


def run_ask(ask: str) -> bool:
    cmd, _, rest = (ask or "").strip().partition(" ")
    return cmd.lower() == "run" and bool(rest.strip())


def fact_lap(row: dict) -> bool:
    if not isinstance(row, dict):
        return False
    if row.get("kind") in ("see", "prove", "duel", "relay", "bench"):
        return False
    if not pure_ask(str(row.get("ask") or "")):
        return False
    if row.get("kind") == "hands":
        return True
    if row.get("seat") == "hands" and row.get("kind") in (None, "", "seat"):
        return True
    return False


def action_lap(row: dict) -> bool:
    if not isinstance(row, dict):
        return False
    if row.get("kind") in ("see", "prove", "duel", "relay", "bench"):
        return False
    if row.get("kind") != "hands" and row.get("seat") != "hands":
        return False
    return run_ask(str(row.get("ask") or ""))


def _short(text: str, limit: int = 120) -> str:
    flat = str(text or "").replace("\n", " ").replace("\r", " ")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 3] + "..."


def _fresh(run_hand, ask: str) -> str:
    try:
        value = run_hand(ask)
    except Exception:
        return "ERROR: could not re-run"
    if value is None:
        return "ERROR: no longer a fact"
    return str(value)


def judge(rows: list[dict], run_hand) -> dict:
    facts = [row for row in rows if fact_lap(row)]
    clipped = len(facts) > 500
    if clipped:
        facts = facts[-500:]
    witnessed = 0
    drifted = []
    tampered = []
    for row in facts:
        ask = str(row.get("ask") or "")
        stored = str(row.get("did") or "")
        on_file = str(row.get("stamp") or "")
        mismatch = bool(on_file) and on_file != stamp_of(ask, stored)
        fresh = _fresh(run_hand, ask)
        ghost = {
            "lap": row.get("lap") or "?",
            "ask": ask,
            "was": _short(stored),
            "now": _short(fresh),
        }
        if mismatch:
            ghost["how"] = "tampered"
            ghost["file_stamp"] = on_file
            ghost["line_stamp"] = stamp_of(ask, stored)
            tampered.append(ghost)
        elif fresh != stored:
            ghost["how"] = "drifted"
            drifted.append(ghost)
        else:
            witnessed += 1
    alone = sum(1 for row in rows if action_lap(row))
    if tampered:
        proof = "tampered"
    elif drifted:
        proof = "drifted"
    elif witnessed:
        proof = "witnessed"
    else:
        proof = "empty"
    lines = [
        f"facts checked    {len(facts)}",
        f"witnessed        {witnessed}",
        f"drifted          {len(drifted)}",
        f"tampered         {len(tampered)}",
        f"runs left alone  {alone}",
        "model laps are not re-run. a model is not a fact.",
    ]
    if clipped:
        lines.append("checked the latest 500 fact laps")
    if proof == "empty":
        lines.append("no fact laps yet")
    for ghost in (tampered + drifted)[:6]:
        lines.append(f"lap {ghost['lap']} {ghost['how']}")
        lines.append(f"was {ghost['was']}")
        lines.append(f"now {ghost['now']}")
        if ghost.get("file_stamp"):
            lines.append(f"file {ghost['file_stamp']}")
            lines.append(f"line {ghost['line_stamp']}")
    return {
        "checked": len(facts),
        "witnessed": witnessed,
        "drifted": len(drifted),
        "tampered": len(tampered),
        "alone": alone,
        "proof": proof,
        "did": "\n".join(lines),
        "ghosts": (tampered + drifted)[:6],
    }
