"""Separate independent verifier required; maker does not self-certify."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Verification:
    status: str
    subject_sha256: str | None
    independent: bool

def pending(subject_sha256: str | None) -> Verification:
    return Verification("NOT_RUN", subject_sha256, False)
