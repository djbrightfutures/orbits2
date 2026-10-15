"""Command line for Orbits 2."""

from __future__ import annotations

import sys

from .desk import emit, live, perform


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["live"]:
        return live()
    code, text = perform(args)
    emit(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
