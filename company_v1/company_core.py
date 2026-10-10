"""Pure deterministic project/task selection; no effects."""
from dataclasses import dataclass
from typing import Iterable
from .models import Task, AuthorityVerifier, DenyAllVerifier

@dataclass(frozen=True)
class Selection:
    task: Task | None
    reason: str
    dispatch_allowed: bool = False

def choose(tasks: Iterable[Task], now: int, verifier: AuthorityVerifier | None = None) -> Selection:
    verifier = verifier if verifier is not None else DenyAllVerifier()
    tasks = tuple(tasks)
    identities = [(t.project_id, t.task_id) for t in tasks]
    if len(identities) != len(set(identities)):
        return Selection(None, "DUPLICATE_TASK_ID")
    eligible = []
    for t in tasks:
        if not t.valid_identity() or t.owner_required or t.security_hold or t.revoked:
            continue
        if now >= t.expires_at:
            continue
        eligible.append(t)
    if not eligible:
        return Selection(None, "NO_VERIFIED_ELIGIBLE_TASK")
    eligible.sort(key=lambda t: (-t.priority, t.project_id, t.task_id))
    for candidate in eligible:
        if verifier.verify(candidate, now):
            return Selection(candidate, "SYNTHETIC_SELECTION_ONLY")
    return Selection(None, "NO_VERIFIED_ELIGIBLE_TASK")
