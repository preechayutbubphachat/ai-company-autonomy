"""Supervisor is infrastructure, not Agent #6; no direct dispatch."""
from dataclasses import dataclass
from .company_core import choose
from .models import AuthorityVerifier, Task

@dataclass(frozen=True)
class WakeRequest:
    request_rin: bool
    candidate: str | None
    reason: str
    dispatch_allowed: bool = False

def tick(tasks: list[Task], now: int, verifier: AuthorityVerifier | None = None) -> WakeRequest:
    result = choose(tasks, now, verifier)
    if result.task is None:
        return WakeRequest(False,None,result.reason)
    return WakeRequest(True,f"{result.task.project_id}/{result.task.task_id}",
                       "REQUEST_GOVERNOR_REVIEW_ONLY")
