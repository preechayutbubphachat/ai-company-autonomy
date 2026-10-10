# Authority Verification & Revocation V1 — candidate contract

**Status:** CHATGPT_OFFHOST_MAKER_CANDIDATE_ONLY; THEMIS_NOT_RUN; no live dispatch.

The exact signed envelope fields are: version, issuer, key_id, audience, project_id, task_id, action, revision, issued_at, not_before, expires_at, nonce. Unknown or missing fields are rejected. Version=1; revision>0; issued_at<=not_before<expires_at; now must be at least issued_at/not_before and less than expires_at. No clock skew. Canonical signed bytes: Python json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii"). Signature: strict base64 Ed25519 (64 bytes). Cross-language canonicalization is not independently certified.

Trust roots are explicit Ed25519 public keys indexed by (issuer,key_id). Revoked issuers, keys and grants are caller-provided immutable snapshots. There is no authenticated key distribution or revocation feed. Rotation requires a new trusted key ID and revocation of the old key. Fail closed for missing/invalid signature, wrong scope, invalid time, revocation, nonce reuse and store error.

TestOnlyReplayStore uses SQLite BEGIN IMMEDIATE and unique (project_id,issuer,nonce). Single-use grants may be consumed even if downstream work fails. No production LF5 durability, crash/power-loss, backup/restore, multi-host or thread-safety certification. No nonce garbage collection.

Existing DenyAllVerifier remains default. No automatic Task adapter to signed grants; new verifier is an explicitly invoked offline API. dispatch_live still raises; GateSnapshot always denies real execution. Five canonical agents unchanged.

**Dependency:** cryptography==46.0.4 (maker environment observed; wheel provenance, hash-locked transitive dependencies and reproducible lock **not established**). Ephemeral keys in tests only. Python 3.13.5 maker environment.

**Holds:** LF3=BLOCKED, LF4=UNVERIFIED, LF5=NOT_PROVEN, A2=BLOCKED_FORMALLY_PARKED_AT_C0. No Donkkub execution, CI, merge, deployment or live agent dispatch.
