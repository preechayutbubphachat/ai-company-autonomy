# Authority V1 maker checkpoint — 2026-10-10

Project: AI-COMPANY-AUTONOMY. North Star: AUTONOMOUS_MULTI_PROJECT_AI_COMPANY_OPERATIONAL.

## Scope completed (ChatGPT connector writer, NOT HERMES)
- Ed25519 signed-envelope verifier with explicit public-key trust roots, issuer/key/grant revocation snapshots, strict scope/time checks and one-use nonce.
- TestOnlyReplayStore with SQLite unique key and BEGIN IMMEDIATE.
- SignedTaskAuthorityAdapter for synthetic choose() path; task expiry and issuer bound to signed envelope.
- Offline test files using ephemeral generated Ed25519 keys.

## Critical status
- Candidate branch only; main and frozen base unchanged.
- Latest candidate commit: 36b209c7df134205e9338492b9a434a2903640ae.
- **Post-commit tests: NOT RUN.** The current tool environment cannot fetch GitHub into its isolated shell; GitHub connector writes/readback are separate. Previous maker 58/58 report is not a certification of this latest commit.
- **Dependency provenance/hash lock: NOT ESTABLISHED.** requirements-authority-v1.txt records version only.
- **THEMIS independent review: NOT RUN**; route unavailable.
- **HERMES writer route: UNAVAILABLE**; work was performed by explicitly authorized ChatGPT offhost maker.
- Live dispatch stays unimplemented and blocked.
- LF3=BLOCKED; LF4=UNVERIFIED; LF5=NOT_PROVEN; A2=BLOCKED_FORMALLY_PARKED_AT_C0.

## Known limitations to resolve before any production consideration
1. No authenticated/rotating revocation feed, no trusted issuer/key distribution lifecycle.
2. TestOnlyReplayStore is not LF5-certified for power loss, multiprocess/multihost or recovery; concurrent use of one SQLite connection is not thread-safe.
3. One-use nonce is consumed during synthetic task selection, not actual dispatch, which can burn an authority without doing work.
4. Canonical JSON contract is Python-specific and cross-language canonicalization is unproven.
5. There is no verified hermetic dependency lock or reproducible installation.
6. No actual agent execution or OS-level project isolation.

## Next bounded work
Read the exact candidate commit; execute focused tests plus full baseline in an authorized isolated offhost workspace with pinned, integrity-checked dependencies; capture commands/logs and source hashes. Resolve any failures on candidate branch only. Request independent read-only THEMIS review only when route is evidenced. Never merge, deploy or dispatch.
