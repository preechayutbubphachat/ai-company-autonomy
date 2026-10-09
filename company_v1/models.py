"""Explicit non-production contracts derived from CS0-CS9."""
from dataclasses import dataclass
from typing import Protocol

CANONICAL_PROFILES = frozenset({"rin-v2", "athena", "hermes-exec", "themis-v1", "mira-v1"})

@dataclass(frozen=True)
class Task:
    project_id: str
    task_id: str
    action: str
    priority: int
    authority_revision: int
    issuer_id: str
    expires_at: int
    owner_required: bool = False
    security_hold: bool = False
    revoked: bool = False
    source_version: int = 1

    def valid_identity(self):
        return (bool(self.project_id.strip()) and bool(self.task_id.strip())
                and bool(self.action.strip()) and bool(self.issuer_id.strip())
                and self.authority_revision > 0 and self.source_version > 0)

class AuthorityVerifier(Protocol):
    def verify(self, task: Task, now: int) -> bool: ...

class DenyAllVerifier:
    """Production-safe default: no registered trust root, no authorization."""
    def verify(self, task: Task, now: int) -> bool:
        return False

class TestOnlyVerifier:
    """Test fixture, NOT cryptographic authority and NEVER for live work."""
    def __init__(self, accepted: set[tuple[str, str, str, int]]):
        self.accepted = frozenset(accepted)

    def verify(self, task: Task, now: int) -> bool:
        return (task.valid_identity() and task.expires_at > now and not task.revoked
                and (task.issuer_id, task.project_id, task.action, task.authority_revision)
                in self.accepted)
