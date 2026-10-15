"""Command line for Orbits 2."""

from __future__ import annotations

import sys

from . import __version__
from . import seats
from .desk import bench, turn
from .hands import hands
from .orbit import tail


HELP = """orbits2 {version}

hands before the model. one orbit file every brain can resume.

  python -m orbits2 bench
  python -m orbits2 seats
  python -m orbits2 tail
  python -m orbits2 hands hostname
  python -m orbits2 ask --seat ollama what is 2 plus 2
  python -m orbits2 hostname

A fact or a run stays in this process. Any other line goes to the seat.
The seat's text is printed as it arrived.
""".format(version=__version__)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(HELP, end="")
        return 0
    if args[0] == "bench":
        result = bench()
        print(
            f"hands {result['hands_ms']:.1f} ms   "
            f"hop {result['hop_ms']:.1f} ms   n={result['n']}"
        )
        return 0 if result["hands_faster"] else 1
    if args[0] == "seats":
        for name in seats.known():
            url = seats.url_for(name) or "set ORBITS2_{}_URL".format(name.upper())
            print(f"{name}  {url}  model {seats.model_for(name)}")
        return 0
    if args[0] == "tail":
        rows = tail(12)
        if not rows:
            print("orbit is empty")
            return 0
        for row in rows:
            print(f"{row.get('seat')}  {row.get('ms')} ms  {row.get('ask')}")
        return 0
    if args[0] == "hands":
        text = " ".join(args[1:]).strip()
        out = hands(text)
        if out is None:
            print("not a hand")
            return 2
        print(out)
        return 0
    if args[0] == "ask":
        seat = None
        rest = args[1:]
        if len(rest) >= 2 and rest[0] == "--seat":
            seat = rest[1]
            rest = rest[2:]
        text = " ".join(rest).strip()
        if not text:
            print(HELP, end="")
            return 2
        print(turn(text, seat=seat))
        return 0
    print(turn(" ".join(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
