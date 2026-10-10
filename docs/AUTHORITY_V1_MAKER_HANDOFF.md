# Authority verification and revocation V1 — offhost candidate

Base: `05afc1c4fb171221ff755f6bfb3dc93710f87301`
Project: `AI-COMPANY-AUTONOMY`
Status: `WRITER_ROUTE_UNAVAILABLE_TO_RIN`; `THEMIS_NOT_RUN`.

This branch is a nonproduction handoff for an **authorized offhost maker**. Creating this branch using the ChatGPT GitHub connector **does not establish** a HERMES writer route or independently verified offhost execution environment.

## Bounded implementation scope
- Add `company_v1/authority_registry.py`.
- Modify `company_v1/models.py` and `company_v1/company_core.py` only as necessary.
- Add focused tests and a versioned authority contract.
- Use a maintained, pinned cryptographic dependency with provenance and integrity recorded before test execution.
- Define canonical signed bytes, issuer and key IDs, audience/project/task/action/revision, validity window, nonce, key rotation, issuer/key revocation and durable atomic replay check-and-record.
- Fail closed on malformed inputs, unknown/revoked issuer/key, altered payload, invalid signature, wrong scope/revision, future/expired grant, replay, store error and concurrent races.
- Ephemeral test keys only; never use production credentials or enable live dispatch.

## Gate and verification rules
Maker evidence is `MAKER_TESTED_ONLY`; independent THEMIS review requires a separately evidenced route and isolated workspace. Do not call this branch LF4-trusted or deployable.

`LF3=BLOCKED`; `LF4=UNVERIFIED`; `LF5=NOT_PROVEN`; `A2=BLOCKED_FORMALLY_PARKED_AT_C0`.

No Donkkub execution, CI, merge, deploy, real dispatch, or changes to child projects.

## Immediate route decision
RIN must either bind a real authorized HERMES offhost writer route or report `OFFHOST_MAKER_ROUTE_UNAVAILABLE`. ChatGPT connector is a distinct writer identity; do not impersonate HERMES or claim its maker verification.
