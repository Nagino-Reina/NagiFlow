"""`nagiflow` CLI — the one-click launcher entry point (docs/13 §3).

  nagiflow up            start backend + frontend (dev), single-terminal logs
  nagiflow up --prod     build the SPA and serve it from FastAPI (one process)
  nagiflow check         run prerequisite checks only

The heavy lifting (process management, log multiplexing, health-wait, graceful
shutdown of NagiFlow's own children) lives in `launcher`.
"""

from __future__ import annotations

import argparse
import sys

from . import launcher


def main() -> None:
    parser = argparse.ArgumentParser(prog="nagiflow", description="NagiFlow local launcher")
    sub = parser.add_subparsers(dest="command")

    up = sub.add_parser("up", help="Start NagiFlow (backend + frontend)")
    up.add_argument("--prod", action="store_true", help="Build the SPA and serve it from FastAPI")
    up.add_argument("--no-browser", action="store_true", help="Do not open the browser")

    sub.add_parser("check", help="Run prerequisite checks and exit")

    args = parser.parse_args()

    if args.command == "check":
        ok = launcher._report(launcher.check_prerequisites(need_frontend=True))
        sys.exit(0 if ok else 1)

    # Default to `up`.
    prod = getattr(args, "prod", False)
    open_browser = not getattr(args, "no_browser", False)
    sys.exit(launcher.up(prod=prod, open_browser=open_browser))


if __name__ == "__main__":
    main()
