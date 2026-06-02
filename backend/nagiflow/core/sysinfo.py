"""Local system-resource snapshot (docs/12 §2.1, FR-OBS-1).

CPU / memory / disk via psutil; GPU via pynvml when present (degrades gracefully to an empty
list otherwise — GPU panels only appear when a GPU is detected). A live snapshot only; short-
term trend samples (`metric_sample`) are a later addition.
"""

from __future__ import annotations

from pathlib import Path

import psutil


def _gpus() -> list[dict]:
    """Per-GPU utilization/VRAM via pynvml; empty when unavailable (no hard dependency)."""
    try:
        import pynvml  # noqa: PLC0415 — optional, imported only when present
    except ImportError:
        return []
    gpus: list[dict] = []
    try:
        pynvml.nvmlInit()
        for i in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            name = pynvml.nvmlDeviceGetName(handle)
            gpus.append(
                {
                    "name": name.decode() if isinstance(name, bytes) else name,
                    "utilization_percent": float(util.gpu),
                    "memory_used": int(mem.used),
                    "memory_total": int(mem.total),
                }
            )
        pynvml.nvmlShutdown()
    except Exception:  # noqa: BLE001 — any NVML error → report no GPUs
        return []
    return gpus


def resource_snapshot(workspace_dir: Path) -> dict:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(str(workspace_dir if workspace_dir.exists() else Path.cwd()))
    proc = psutil.Process()
    cpu_count = psutil.cpu_count()
    # Coerce to plain Python scalars: some psutil/pynvml builds return numpy types, which are
    # not JSON-serializable and would break the status stream's send_json (docs/05 §5.1).
    return {
        "cpu_percent": float(psutil.cpu_percent(interval=None)),
        "cpu_count": int(cpu_count) if cpu_count is not None else None,
        "memory": {
            "used": int(vm.used),
            "total": int(vm.total),
            "percent": float(vm.percent),
        },
        "disk": {
            "used": int(disk.used),
            "total": int(disk.total),
            "free": int(disk.free),
            "percent": float(disk.percent),
        },
        "process": {
            "pid": int(proc.pid),
            "rss": int(proc.memory_info().rss),
        },
        "gpus": _gpus(),
    }
