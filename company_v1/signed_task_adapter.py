"""One-use signed authority binding for synthetic task selection only.

Never enables live dispatch. The verifier consumes a nonce when choose() verifies a task.
"""
from .authority_registry import AuthorityRequest, SignedAuthorityVerifier
from .models import Task

class SignedTaskAuthorityAdapter:
    def __init__(self, verifier: SignedAuthorityVerifier, grants: dict[tuple[str,str],tuple[dict,str]], audience: str):
        self.verifier = verifier
        self.grants = dict(grants)
        self.audience = audience

    def verify(self, task: Task, now: int) -> bool:
        if not task.valid_identity() or task.revoked or task.security_hold or task.owner_required:
            return False
        if type(now) is not int or now >= task.expires_at:
            return False
        pair = self.grants.get((task.project_id,task.task_id))
        if type(pair) is not tuple or len(pair) != 2:
            return False
        envelope, signature = pair
        if type(envelope) is not dict or envelope.get("issuer") != task.issuer_id:
            return False
        if envelope.get("expires_at") != task.expires_at:
            return False
        request = AuthorityRequest(self.audience,task.project_id,task.task_id,task.action,task.authority_revision)
        return self.verifier.verify_envelope(envelope,signature,request,now)
