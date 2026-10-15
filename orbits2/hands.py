"""Computer facts and commands that do not need a model.

A sentence returns None so the desk can hand it to a seat. A fact returns the
answer from this process. A run uses an argument list, never a shell string.
"""

from __future__ import annotations

import os
import shlex
import shutil
import socket
import subprocess
from pathlib import Path

_RUN = None  # tests can replace the runner


def _run(argv: list[str]) -> str:
    if _RUN is not None:
        return _RUN(argv)
    try:
        done = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: the command took more than 8 seconds"
    except OSError as exc:
        return f"ERROR: {exc.strerror or exc}"
    text = (done.stdout or "") + (done.stderr or "")
    text = text.strip()
    if done.returncode != 0:
        return text or f"ERROR: exit {done.returncode}"
    return text


def hands(text: str) -> str | None:
    """Return the computer's answer, or None when this line needs a brain."""
    raw = (text or "").strip()
    if not raw or raw.startswith("/") or len(raw) > 2000:
        return None
    cmd, _, rest = raw.partition(" ")
    cmd = cmd.lower()
    rest = rest.strip()
    if cmd == "hostname" and not rest:
        return socket.gethostname()
    if cmd == "whoami" and not rest:
        return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    if cmd == "cwd" and not rest:
        return str(Path.cwd())
    if cmd == "disk" and not rest:
        usage = shutil.disk_usage(Path.cwd())
        free = usage.free / (1024 ** 3)
        total = usage.total / (1024 ** 3)
        return f"{free:.1f} GB free of {total:.1f} GB"
    if cmd == "list" and rest:
        folder = Path(rest.strip('"'))
        if not folder.is_dir():
            return "ERROR: that folder is not here"
        names = sorted(p.name for p in folder.iterdir())
        shown = names[:200]
        extra = "" if len(names) <= 200 else f"\n... {len(names) - 200} more"
        return "\n".join(shown) + extra
    if cmd == "read" and rest:
        file_path = Path(rest.strip('"'))
        if not file_path.is_file():
            return "ERROR: that file is not here"
        data = file_path.read_text(encoding="utf-8", errors="replace")
        if len(data) > 20000:
            return data[:20000] + "\n... truncated"
        return data
    if cmd == "run" and rest:
        try:
            argv = shlex.split(rest, posix=True)
        except ValueError:
            return "ERROR: could not read that command"
        if not argv:
            return None
        return _run(argv)
    return None
