"""In-process JobRunner skeleton (docs/03 §8 ADR-004, docs/04 §6).

Long work (ASR import, render, fine-tune, re-embed) runs as tracked asyncio tasks with
status/progress/cancellation. P0 provides the seam + in-memory tracking; persistence to the
`job` table and the full job API land with the features that need them (P2+).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ..core.ids import new_id
from ..core.logging import get_logger

log = get_logger("nagiflow.jobs")


@dataclass
class Job:
    id: str
    type: str
    status: str = "pending"  # pending|running|succeeded|failed|cancelled
    progress: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
    _task: asyncio.Task | None = field(default=None, repr=False)


JobFn = Callable[["Job"], Awaitable[dict[str, Any] | None]]


class JobRunner:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def submit(self, job_type: str, fn: JobFn) -> Job:
        job = Job(id=new_id("job"), type=job_type)
        self._jobs[job.id] = job
        job._task = asyncio.create_task(self._run(job, fn))
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job._task and not job._task.done():
            job._task.cancel()
            return True
        return False

    async def _run(self, job: Job, fn: JobFn) -> None:
        job.status = "running"
        try:
            job.result = await fn(job)
            job.status = "succeeded"
            job.progress = 1.0
        except asyncio.CancelledError:
            job.status = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced as job error
            job.status = "failed"
            job.error = str(exc)
            log.exception("job %s (%s) failed", job.id, job.type)


job_runner = JobRunner()
