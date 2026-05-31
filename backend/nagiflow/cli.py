"""`nagiflow` CLI — minimal launcher seam (docs/13 §3).

`nagiflow up` runs the backend (uvicorn). The full prereq-checking, log-multiplexing,
graceful-shutdown launcher (docs/13) builds on this entry point.
"""

from __future__ import annotations

import argparse

from .config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="nagiflow", description="NagiFlow backend launcher")
    sub = parser.add_subparsers(dest="command")

    up = sub.add_parser("up", help="Run the backend server")
    up.add_argument("--reload", action="store_true", help="Auto-reload (dev)")

    args = parser.parse_args()
    settings = get_settings()

    if args.command == "up" or args.command is None:
        import uvicorn

        uvicorn.run(
            "nagiflow.main:app",
            host=settings.host,
            port=settings.port,
            reload=getattr(args, "reload", False),
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
