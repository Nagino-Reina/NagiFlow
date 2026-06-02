"""`nagiflow` CLI -- the one-click launcher entry point (docs/14 §3).

  nagiflow up            start backend + frontend (dev), single-terminal logs
  nagiflow up --prod     build the SPA and serve it from FastAPI (one process)
  nagiflow check         run prerequisite checks only

The heavy lifting (process management, log multiplexing, health-wait, graceful
shutdown of NagiFlow's own children) lives in `launcher`.
"""

from __future__ import annotations

from typing import Annotated

import typer

from . import launcher

app = typer.Typer(
    name="nagiflow",
    help="NagiFlow local launcher",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """Run `up` with defaults when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        raise typer.Exit(launcher.up())


@app.command()
def up(
    prod: Annotated[
        bool,
        typer.Option(help="Build the SPA and serve it from FastAPI (one process)."),
    ] = False,
    browser: Annotated[
        bool,
        typer.Option("--browser/--no-browser", help="Open the app in a browser when ready."),
    ] = True,
) -> None:
    """Start NagiFlow (backend + frontend) with single-terminal logs."""
    raise typer.Exit(launcher.up(prod=prod, open_browser=browser))


@app.command()
def check() -> None:
    """Run prerequisite checks and exit."""
    raise typer.Exit(0 if launcher.run_prerequisite_check(need_frontend=True) else 1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
