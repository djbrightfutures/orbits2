"""The pit card.

ASCII only, so a Windows console that is still on cp1252 can print the frame.
Model text is wrapped for the card. The orbit file keeps the original line.
"""

from __future__ import annotations

W = 62

KIND = {
    "hands": "HANDS",
    "seat": "SEAT",
    "duel": "DUEL",
    "relay": "RELAY",
    "see": "SEE",
    "prove": "PROVE",
    "bench": "BENCH",
}

STATUS = {
    "unchecked": "RAN",
    "machine": "MACHINE",
    "model": "RAW",
    "race": "RACE",
    "tie": "TIE",
    "dark": "DARK",
    "relay": "RELAY",
    "witnessed": "WITNESSED",
    "drifted": "DRIFTED",
    "tampered": "TAMPERED",
    "empty": "EMPTY",
}


def _rule() -> str:
    return "+" + ("-" * W) + "+"


def _row(text: str) -> str:
    shown = "" if text is None else str(text)
    if len(shown) > W:
        shown = shown[: W - 1] + ">"
    return "|" + shown.ljust(W) + "|"


def _pair(left: str, right: str) -> str:
    left = (left or "").strip()
    right = (right or "").strip()
    if right:
        left = left[: max(0, W - 3 - len(right))]
        gap = W - 2 - len(left) - len(right)
        return " " + left + (" " * max(1, gap)) + right + " "
    text = " " + left
    if len(text) > W:
        return text[: W - 1] + ">"
    return text


def _ms(value) -> str:
    try:
        return f"{float(value):.2f} ms"
    except (TypeError, ValueError):
        return "0.00 ms"


def _lap(value) -> str:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "--"
    if n < 100:
        return f"{n:02d}"
    return str(n)


def _chunks(text: str, width: int, limit: int) -> list[str]:
    raw = str(text or "").replace("\t", " ").replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for para in raw.split("\n"):
        if para == "":
            lines.append("")
            continue
        while len(para) > width:
            lines.append(para[:width])
            para = para[width:]
        lines.append(para)
    if not lines:
        lines = [""]
    if len(lines) > limit:
        lines = lines[:limit]
        lines.append("... full line is in the orbit")
    return lines


def _panel(lines: list[str]) -> str:
    out = [_rule()]
    out.extend(_row(line) for line in lines)
    out.append(_rule())
    return "\n".join(out)


def banner() -> str:
    return _panel([
        "",
        _pair("ORBITS 2  /  THE PIT", ""),
        " hands before the model",
        " one orbit file. every brain resumes. nothing is rewritten.",
        "",
    ])


def panel(title: str, lines: list[str]) -> str:
    out = [
        _rule(),
        _row(_pair("ORBITS 2  /  THE PIT", title)),
        _rule(),
    ]
    for line in lines:
        for chunk in _chunks(line.strip(), W - 1, 6):
            out.append(_row((" " + chunk) if chunk else ""))
    out.append(_rule())
    return "\n".join(out)


def _tag(row: dict) -> str:
    kind = str(row.get("kind") or "")
    proof = str(row.get("proof") or "")
    if kind == "prove":
        return {
            "witnessed": "HELD",
            "drifted": "DRIFT",
            "tampered": "TAMPER",
            "empty": "NONE",
        }.get(proof, "PROVE")
    if kind == "duel":
        return {"tie": "TIE", "dark": "DARK"}.get(proof, "RACE")
    return {
        "hands": "RAN",
        "seat": "RAW",
        "relay": "RLAY",
        "see": "SEE",
        "bench": "BENCH",
    }.get(kind, "LAP")


def belt(rows: list[dict]) -> str:
    parts = []
    for row in rows[-8:]:
        parts.append(f"{_lap(row.get('lap'))} {_tag(row)} {_ms(row.get('ms')).replace(' ms', '')}")
    return " " + "  ".join(parts)


def _block(label: str, text: str, limit: int) -> list[str]:
    lines = [f" {label}"]
    for chunk in _chunks(text, W - 1, limit):
        lines.append((" " + chunk) if chunk else "")
    return lines


def _field(racers: list, winner: str = "") -> list[str]:
    from .seats import is_dark

    lines: list[str] = [" FIELD"]
    if not racers:
        lines.append(" no racers")
        return lines
    for racer in racers[:8]:
        if not isinstance(racer, dict):
            continue
        did = str(racer.get("did") or "")
        seat = str(racer.get("seat") or "")
        if is_dark(did):
            mark = "DARK"
        elif winner and seat == winner:
            mark = "WIN"
        else:
            mark = "LIVE"
        lines.append(_pair(f"{seat}  {_ms(racer.get('ms'))}", mark))
        for chunk in _chunks(did, W - 3, 3):
            lines.append(("   " + chunk) if chunk else "")
    return lines


def card(row: dict, crown: str = "") -> str:
    kind = KIND.get(str(row.get("kind") or ""), "LAP")
    status = STATUS.get(str(row.get("proof") or ""), "LAP")
    lines = [
        _rule(),
        _row(_pair("ORBITS 2  /  THE PIT", f"lap {_lap(row.get('lap'))}")),
        _row(_pair(kind, status)),
        _rule(),
        _row(f" {_ms(row.get('ms'))}"),
        _row(f" crown {crown or 'none'}"),
        _rule(),
    ]
    kind_name = str(row.get("kind") or "")
    if kind_name in ("duel", "relay"):
        lines.extend(_row(line) for line in _field(row.get("racers") or [], str(row.get("winner") or "")))
    elif kind_name == "see":
        lines.extend(_row(line) for line in _block("MACHINE", str(row.get("did") or ""), 12))
    elif kind_name == "prove":
        lines.extend(_row(line) for line in _block("CHECK", str(row.get("did") or ""), 18))
    else:
        lines.extend(_row(line) for line in _block("ASK", str(row.get("ask") or ""), 4))
        lines.extend(_row(line) for line in _block("DID", str(row.get("did") or ""), 8))
    lines.append(_row(""))
    lines.append(_row(f" STAMP  {row.get('stamp') or '-'}"))
    lines.append(_rule())
    return "\n".join(lines)


def board(rows: list[dict], lights: list[dict], crown: str) -> str:
    body = [
        " " + (belt(rows).strip() or "no laps yet"),
        f" crown {crown or 'none'}",
    ]
    if not rows:
        body.append(" no laps yet")
    for row in rows[-8:]:
        ask = str(row.get("ask") or "").replace("\n", " ")
        if len(ask) > 24:
            ask = ask[:23] + ">"
        winner = ""
        if row.get("kind") in ("duel", "relay") and row.get("winner"):
            winner = " " + str(row.get("winner"))
        body.append(
            f" {_lap(row.get('lap'))} {_tag(row):<5} {_ms(row.get('ms')):>10}  {ask}{winner}"
        )
    body.append("")
    if not lights:
        body.append(" no seats")
    for light in lights:
        name = str(light.get("name") or "")
        state = str(light.get("state") or "")
        where = str(light.get("where") or "")
        body.append(f" {name:<10} {state:<6} {where}")
    return panel("BOARD", body)


def tint(text: str) -> str:
    """One color for the whole card. The words do not change."""
    head = "\n".join(text.splitlines()[:6])
    color = "37"
    if any(word in head for word in ("WITNESSED", " RAN", "MACHINE", " HELD")):
        color = "32"
    elif any(word in head for word in ("DRIFTED", "TAMPERED", " DARK")):
        color = "31"
    elif any(word in head for word in ("RACE", "TIE", "RELAY", "BENCH", "BOARD", "SEATS")):
        color = "36"
    elif "RAW" in head:
        color = "33"
    return f"\033[1;{color}m{text}\033[0m"
