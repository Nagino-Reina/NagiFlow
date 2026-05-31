"""One-click local launcher (docs/13 §3, FR-SYS-1…5).

Starts the backend (uvicorn) and, in dev, the frontend (Vite), multiplexes both logs into
a single terminal with colored prefixes, health-waits until ready, and on Ctrl-C / terminal
close tears down **only NagiFlow's own children** — never external services like Ollama.

Cross-platform: POSIX uses sessions + signals; Windows uses a new process group +
CTRL_BREAK_EVENT with a taskkill escalation (docs/13 §3.3).
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings

IS_WIN = os.name == "nt"

# nagiflow/launcher.py -> nagiflow -> backend -> repo root
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_WEB_DIR = _REPO_ROOT / "web"
_DIST_DIR = _WEB_DIR / "dist"

_VITE_PORT = 5173  # keep in sync with web/vite.config.mts


class _C:
    BACKEND = "\033[36m"
    FRONTEND = "\033[35m"
    OK = "\033[32m"
    WARN = "\033[33m"
    ERR = "\033[31m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def _enable_ansi() -> None:
    if IS_WIN:
        os.system("")  # enable VT processing on modern Windows terminals
    # Never let a non-ASCII log line from a child crash our terminal on a legacy codepage.
    try:
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


# --- prerequisites (FR-SYS-2) ---


@dataclass
class Prereq:
    name: str
    ok: bool
    detail: str
    required: bool


def check_prerequisites(*, need_frontend: bool) -> list[Prereq]:
    """Verify tools + versions. Optional deps (ffmpeg, Ollama) are informational."""
    checks: list[Prereq] = [
        Prereq("Python", True, sys.version.split()[0], required=True),
    ]
    node = shutil.which("node")
    pnpm = shutil.which("pnpm")
    checks.append(
        Prereq("Node.js", node is not None, node or "install Node 18+ - https://nodejs.org",
               required=need_frontend)
    )
    checks.append(
        Prereq("pnpm", pnpm is not None, pnpm or "install pnpm - `npm i -g pnpm`",
               required=need_frontend)
    )
    ffmpeg = shutil.which("ffmpeg")
    checks.append(
        Prereq("ffmpeg", ffmpeg is not None, ffmpeg or "optional - media/ASR (P2+)", required=False)
    )
    ollama = shutil.which("ollama")
    checks.append(
        Prereq("Ollama", ollama is not None,
               ollama or "optional - local LLM; offline echo provider used otherwise",
               required=False)
    )
    return checks


def _report(checks: list[Prereq]) -> bool:
    print(f"{_C.BOLD}NagiFlow - prerequisite check{_C.RESET}")
    all_required_ok = True
    for c in checks:
        if c.ok:
            mark, color = "OK  ", _C.OK
        elif c.required:
            mark, color = "MISS", _C.ERR
            all_required_ok = False
        else:
            mark, color = "skip", _C.WARN
        print(f"  {color}[{mark}]{_C.RESET} {c.name:<10} {_C.DIM}{c.detail}{_C.RESET}")
    if not all_required_ok:
        print(f"{_C.ERR}Missing required prerequisites - fix the above and retry.{_C.RESET}")
    return all_required_ok


# --- data safety (FR-SYS-10) ---


def backup_db() -> Path | None:
    """Timestamped DB snapshot to workspace/backups/ before migrations run."""
    settings = get_settings()
    db = settings.db_path
    if not db.exists():
        return None
    backups = settings.workspace_dir / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dst = backups / f"nagiflow-{ts}.db"
    shutil.copy2(db, dst)
    return dst


# --- process management ---


def _popen(cmd: list[str], cwd: Path) -> subprocess.Popen[str]:
    kwargs: dict = {}
    if IS_WIN:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True  # child becomes its own process-group leader
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding="utf-8",
        errors="replace",  # child output (e.g. Vite's unicode) must not crash the pump
        **kwargs,
    )


def _pump(proc: subprocess.Popen[str], prefix: str, color: str) -> threading.Thread:
    def run() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(f"{color}[{prefix}]{_C.RESET} {line.rstrip()}\n")
            sys.stdout.flush()

    t = threading.Thread(target=run, name=f"log-{prefix}", daemon=True)
    t.start()
    return t


def _terminate(name: str, proc: subprocess.Popen[str], color: str) -> None:
    if proc.poll() is not None:
        return
    print(f"{color}[{name}]{_C.RESET} {_C.DIM}stopping...{_C.RESET}")
    try:
        if IS_WIN:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass
    try:
        proc.wait(timeout=8)
        return
    except subprocess.TimeoutExpired:
        pass
    # Escalate.
    try:
        if IS_WIN:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass


# --- health wait (FR-SYS) ---


def _health_url() -> str:
    s = get_settings()
    host = "127.0.0.1" if s.host in {"0.0.0.0", "::"} else s.host
    return f"http://{host}:{s.port}/healthz"


def wait_healthy(timeout: float = 40.0) -> bool:
    url = _health_url()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    return False


# --- frontend build (prod, FR-SYS-3) ---


def build_frontend() -> None:
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise RuntimeError("pnpm not found - cannot build the frontend")
    print(f"{_C.FRONTEND}[frontend]{_C.RESET} installing deps...")
    subprocess.run([pnpm, "install"], cwd=str(_WEB_DIR), check=True)
    print(f"{_C.FRONTEND}[frontend]{_C.RESET} building SPA...")
    subprocess.run([pnpm, "build"], cwd=str(_WEB_DIR), check=True)


# --- orchestration ---


def up(*, prod: bool = False, open_browser: bool = True) -> int:
    _enable_ansi()
    settings = get_settings()

    if not _report(check_prerequisites(need_frontend=True)):
        return 1

    if prod:
        try:
            build_frontend()
        except (subprocess.CalledProcessError, RuntimeError) as exc:
            print(f"{_C.ERR}Frontend build failed: {exc}{_C.RESET}")
            return 1

    bak = backup_db()
    if bak is not None:
        print(f"{_C.DIM}DB backed up -> {bak}{_C.RESET}")

    children: list[tuple[str, subprocess.Popen[str], str]] = []

    backend_cmd = [
        sys.executable, "-m", "uvicorn", "nagiflow.main:app",
        "--host", settings.host, "--port", str(settings.port),
    ]
    backend = _popen(backend_cmd, cwd=_BACKEND_ROOT)
    children.append(("backend", backend, _C.BACKEND))
    _pump(backend, "backend", _C.BACKEND)

    app_url = f"http://127.0.0.1:{settings.port}"
    if not prod:
        pnpm = shutil.which("pnpm")
        assert pnpm is not None  # guaranteed by prereq check
        frontend = _popen([pnpm, "dev"], cwd=_WEB_DIR)
        children.append(("frontend", frontend, _C.FRONTEND))
        _pump(frontend, "frontend", _C.FRONTEND)
        app_url = f"http://localhost:{_VITE_PORT}"

    if wait_healthy():
        print(f"{_C.OK}{_C.BOLD}NagiFlow is up -> {app_url}{_C.RESET}")
        if open_browser:
            webbrowser.open(app_url)
    else:
        print(f"{_C.WARN}Backend did not report healthy in time; logs continue below.{_C.RESET}")

    return _run_until_exit(children)


def _run_until_exit(children: list[tuple[str, subprocess.Popen[str], str]]) -> int:
    stop = threading.Event()

    def handler(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    if IS_WIN and hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handler)  # type: ignore[attr-defined]

    exit_code = 0
    while not stop.is_set():
        for name, proc, color in children:
            if proc.poll() is not None:
                print(f"{color}[{name}]{_C.RESET} {_C.WARN}exited (code {proc.returncode}); "
                      f"shutting down.{_C.RESET}")
                exit_code = proc.returncode or 0
                stop.set()
                break
        time.sleep(0.5)

    print(f"\n{_C.DIM}Shutting down NagiFlow (external services left running)...{_C.RESET}")
    for name, proc, color in children:
        _terminate(name, proc, color)
    return exit_code
