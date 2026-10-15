"""Brain seats.

Each seat is an OpenAI-compatible chat endpoint. The text that comes back is
returned as the seat wrote it. This module does not score it, rewrite it, or
send it through a moderation call.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_OPEN = None  # tests can replace the HTTP call

_DEFAULTS = {
    "ollama": "http://127.0.0.1:11434/v1",
    "cleen": "http://127.0.0.1:8088/v1",
    "openai": "https://api.openai.com/v1",
    "grok": "https://api.x.ai/v1",
}

_MODELS = {
    "ollama": "qwen2.5-coder:7b",
    "cleen": "cleen-chat",
    "openai": "gpt-4o-mini",
    "grok": "grok-4",
    "opencode": "opencode",
    "hermes": "hermes",
    "openclaw": "openclaw",
}


def known() -> list[str]:
    return ["ollama", "cleen", "openai", "grok", "opencode", "hermes", "openclaw"]


def url_for(name: str) -> str | None:
    key = (name or "").strip().lower()
    env = os.environ.get(f"ORBITS2_{key.upper()}_URL", "").strip()
    if env:
        return env.rstrip("/")
    return _DEFAULTS.get(key)


def model_for(name: str) -> str:
    key = (name or "").strip().lower()
    env = os.environ.get(f"ORBITS2_{key.upper()}_MODEL", "").strip()
    if env:
        return env
    shared = os.environ.get("ORBITS2_MODEL", "").strip()
    if shared and key in ("opencode", "hermes", "openclaw"):
        return shared
    return _MODELS.get(key, key or "local")


def key_for(name: str) -> str:
    key = (name or "").strip().lower()
    specific = os.environ.get(f"ORBITS2_{key.upper()}_KEY", "").strip()
    if specific:
        return specific
    if key == "openai":
        return os.environ.get("OPENAI_API_KEY", "").strip()
    if key == "grok":
        return os.environ.get("XAI_API_KEY", "").strip()
    return ""


def is_dark(text: str) -> bool:
    return str(text or "").startswith("seat dark:")


def messages(ask: str, recent: list[dict]) -> list[dict]:
    """The ask, plus the orbit tail so the next brain can continue the work.

    Other racers on a duel or a relay are included as they answered. The
    winning line is not rewritten, and it is not pasted a second time.
    """
    body: list[dict] = []
    if recent:
        lines = []
        for row in recent:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('seat')}: {row.get('ask')} -> {row.get('did')}")
            main = str(row.get("did") or "")
            racers = row.get("racers") or []
            if not isinstance(racers, list):
                continue
            for racer in racers[:8]:
                if not isinstance(racer, dict):
                    continue
                bit = str(racer.get("did") or "")
                if not bit or bit == main:
                    continue
                lines.append(f"  - {racer.get('seat')}: {bit[:500]}")
        body.append({
            "role": "system",
            "content": "Recent orbit, oldest first. Continue this work.\n" + "\n".join(lines),
        })
    body.append({"role": "user", "content": ask})
    return body


def ask(name: str, chat: list[dict], timeout: float = 30) -> str:
    """One completion. Dark seats return a short status. Model text is unchanged."""
    key_name = (name or "").strip().lower()
    base = url_for(key_name)
    if not base:
        return f"seat dark: {key_name} has no url"
    payload = json.dumps({
        "model": model_for(key_name),
        "messages": chat,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = key_for(key_name)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        base + "/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )
    opener = _OPEN or urllib.request.urlopen
    try:
        with opener(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return f"seat dark: {key_name}"
    try:
        data = json.loads(raw)
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return raw
    if text is None:
        return ""
    return text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
