"""Background job runner (docs/03 §5, docs/04 §6) — in-process, no mandatory broker."""

from .runner import Job, JobRunner, job_runner

__all__ = ["Job", "JobRunner", "job_runner"]
