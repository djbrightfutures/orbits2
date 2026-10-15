"""Seat races.

The fastest answer that is not a dark seat wins. Every racer stays on the
card with a time. Model text is returned as the seat wrote it.
"""

from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from . import seats

MAX_RACE = 8
MAX_RELAY = 4


def _parts(url: str) -> tuple[str, int, str]:
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    if parsed.port:
        port = parsed.port
    elif parsed.scheme == "https":
        port = 443
    else:
        port = 80
    show = f"{host}:{port}" if host else "no url"
    return host, port, show


def public_where(url: str | None) -> str:
    """Host and port only. A key or a user in the URL is not shown."""
    if not url:
        return "no url"
    _host, _port, show = _parts(url)
    return show


def is_local(url: str | None) -> bool:
    if not url:
        return False
    host, _port, _show = _parts(url)
    return host.lower() in ("127.0.0.1", "localhost", "::1")


def tcp(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


def lights(probe=None) -> list[dict]:
    """Awake, dark, or keyed. A keyed cloud seat is not contacted."""
    check = probe or tcp
    out: list[dict] = []
    for name in seats.known():
        url = seats.url_for(name)
        if not url:
            out.append({"name": name, "state": "dark", "where": "no url"})
            continue
        where = public_where(url)
        if is_local(url):
            host, port, _show = _parts(url)
            try:
                ok = bool(check(host, port))
            except Exception:
                ok = False
            out.append({"name": name, "state": "awake" if ok else "dark", "where": where})
            continue
        if not seats.key_for(name):
            out.append({"name": name, "state": "dark", "where": "no key"})
            continue
        out.append({"name": name, "state": "keyed", "where": where})
    return out


def awake(probe=None) -> list[str]:
    """Local seats with an open port. Cloud seats wait until they are named."""
    return [row["name"] for row in lights(probe) if row["state"] == "awake"]


def _as_text(value) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _timed(name: str, chat: list, racer) -> dict:
    started = time.perf_counter()
    try:
        did = _as_text(racer(name, list(chat)))
    except Exception:
        did = f"seat dark: {name}"
    return {
        "seat": name,
        "ms": round((time.perf_counter() - started) * 1000, 2),
        "did": did,
    }


def finish_order(racers: list[dict], order: list[str]) -> list[dict]:
    rank = {name: i for i, name in enumerate(order)}

    def key(racer: dict):
        dark = 1 if seats.is_dark(str(racer.get("did") or "")) else 0
        try:
            ms = float(racer.get("ms") or 0)
        except (TypeError, ValueError):
            ms = 0.0
        return (dark, ms, rank.get(str(racer.get("seat") or ""), 10**6))

    return sorted(racers, key=key)


def pick_winner(racers: list[dict], order: list[str]) -> dict | None:
    for racer in finish_order(racers, order):
        if not seats.is_dark(str(racer.get("did") or "")):
            return racer
    return None


def tie_count(racers: list[dict], winner: dict | None) -> int:
    if not winner:
        return 0
    best = winner.get("ms")
    count = 0
    for racer in racers:
        if seats.is_dark(str(racer.get("did") or "")):
            continue
        if racer.get("ms") == best:
            count += 1
    return count


def race(order: list[str], chat: list, racer, timeout: float) -> list[dict]:
    if not order:
        return []
    found: list[dict] = []
    workers = max(1, min(MAX_RACE, len(order)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [(name, pool.submit(_timed, name, chat, racer)) for name in order]
        for name, job in jobs:
            try:
                found.append(job.result(timeout=float(timeout) + 1.0))
            except Exception:
                found.append({
                    "seat": name,
                    "ms": round(float(timeout) * 1000, 2),
                    "did": f"seat dark: {name}",
                })
    return found


def duel_field(ask: str, order: list[str], racer, recent: list[dict], timeout: float = 8.0) -> dict:
    """Race the named seats on the same ask. Wait for the field, then rank it."""
    order = [name for name in order if name][:MAX_RACE]
    if not order:
        return {
            "kind": "duel",
            "seat": "duel",
            "ask": ask,
            "did": "no seat awake",
            "ms": 0,
            "winner": "",
            "proof": "dark",
            "racers": [],
        }
    chat = seats.messages(ask, recent)
    racers = finish_order(race(order, chat, racer, timeout), order)
    winner = pick_winner(racers, order)
    if winner is None:
        return {
            "kind": "duel",
            "seat": "duel",
            "ask": ask,
            "did": "every seat was dark",
            "ms": max((r["ms"] for r in racers), default=0),
            "winner": "",
            "proof": "dark",
            "racers": racers,
        }
    proof = "tie" if tie_count(racers, winner) > 1 else "race"
    return {
        "kind": "duel",
        "seat": winner["seat"],
        "ask": ask,
        "did": winner["did"],
        "ms": winner["ms"],
        "winner": winner["seat"],
        "proof": proof,
        "racers": racers,
    }


def relay_field(ask: str, order: list[str], racer, recent: list[dict]) -> dict:
    """Each named seat sees the previous seat's raw text. Nothing is rewritten."""
    order = [name for name in order if name][:MAX_RELAY]
    chat = seats.messages(ask, recent)
    racers: list[dict] = []
    if not order:
        return {
            "kind": "relay",
            "seat": "relay",
            "ask": ask,
            "did": "no seats named",
            "ms": 0,
            "winner": "",
            "proof": "dark",
            "racers": [],
        }
    for name in order:
        racers.append(_timed(name, chat, racer))
        chat = list(chat) + [{"role": "assistant", "content": racers[-1]["did"]}]
    winner = None
    for racer_row in reversed(racers):
        if not seats.is_dark(racer_row["did"]):
            winner = racer_row
            break
    last = racers[-1]
    return {
        "kind": "relay",
        "seat": last["seat"],
        "ask": ask,
        "did": last["did"],
        "ms": round(sum(r["ms"] for r in racers), 2),
        "winner": "" if winner is None else winner["seat"],
        "proof": "dark" if winner is None else "relay",
        "racers": racers,
    }
