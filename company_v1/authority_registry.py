"""Offline Ed25519 authority checks. Nonproduction; no live dispatch."""
import base64
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

FIELDS = frozenset(("version","issuer","key_id","audience","project_id","task_id","action","revision","issued_at","not_before","expires_at","nonce"))
INTS = frozenset(("version","revision","issued_at","not_before","expires_at"))

def canonical_bytes(envelope):
    if type(envelope) is not dict or set(envelope) != FIELDS:
        raise ValueError("INVALID_FIELDS")
    if any(type(envelope[k]) is not int for k in INTS):
        raise ValueError("INVALID_INTEGER")
    if envelope["version"] != 1 or envelope["revision"] <= 0:
        raise ValueError("INVALID_VERSION")
    if any(type(envelope[k]) is not str or not envelope[k] or len(envelope[k]) > 256 or envelope[k].strip() != envelope[k] for k in FIELDS-INTS):
        raise ValueError("INVALID_TEXT")
    if not (envelope["issued_at"] <= envelope["not_before"] < envelope["expires_at"]):
        raise ValueError("INVALID_TIME")
    return json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")

@dataclass(frozen=True)
class AuthorityRequest:
    audience: str
    project_id: str
    task_id: str
    action: str
    revision: int

class TestOnlyReplayStore:
    """Atomic SQLite nonce consumption; NOT LF5-certified durable storage."""
    def __init__(self,path: str | Path):
        self.conn=sqlite3.connect(str(path),timeout=2,isolation_level=None)
        self.conn.execute("PRAGMA busy_timeout=2000")
        self.conn.execute("CREATE TABLE IF NOT EXISTS used_nonces (project_id TEXT NOT NULL,issuer TEXT NOT NULL,nonce TEXT NOT NULL,PRIMARY KEY(project_id,issuer,nonce))")
    def consume(self,project_id,issuer,nonce):
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.execute("INSERT INTO used_nonces VALUES (?,?,?)",(project_id,issuer,nonce))
            self.conn.execute("COMMIT")
            return True
        except sqlite3.Error:
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK")
            return False
    def close(self):
        self.conn.close()

class SignedAuthorityVerifier:
    """Explicit opt-in trust roots, revocation snapshots and one-use nonce."""
    def __init__(self,trusted_keys,replay_store,*,revoked_issuers=frozenset(),revoked_keys=frozenset(),revoked_grants=frozenset()):
        self.keys=dict(trusted_keys)
        self.store=replay_store
        self.revoked_issuers=frozenset(revoked_issuers)
        self.revoked_keys=frozenset(revoked_keys)
        self.revoked_grants=frozenset(revoked_grants)
    def verify_envelope(self,envelope,signature_b64,request: AuthorityRequest,now: int):
        try:
            if type(now) is not int or type(request.revision) is not int:
                return False
            raw=canonical_bytes(envelope)
            issuer,key_id=envelope["issuer"],envelope["key_id"]
            if issuer in self.revoked_issuers or (issuer,key_id) in self.revoked_keys or (issuer,envelope["project_id"],envelope["nonce"]) in self.revoked_grants:
                return False
            if (envelope["audience"],envelope["project_id"],envelope["task_id"],envelope["action"],envelope["revision"]) != (request.audience,request.project_id,request.task_id,request.action,request.revision):
                return False
            if now < envelope["issued_at"] or now < envelope["not_before"] or now >= envelope["expires_at"]:
                return False
            key=self.keys.get((issuer,key_id))
            if type(key) is not bytes or len(key)!=32 or type(signature_b64) is not str:
                return False
            signature=base64.b64decode(signature_b64,validate=True)
            if len(signature)!=64:
                return False
            Ed25519PublicKey.from_public_bytes(key).verify(signature,raw)
            return self.store.consume(envelope["project_id"],issuer,envelope["nonce"]) is True
        except (ValueError,TypeError,KeyError,InvalidSignature,sqlite3.Error,AttributeError,RuntimeError,OSError):
            return False
