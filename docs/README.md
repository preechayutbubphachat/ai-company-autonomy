# AI-COMPANY-AUTONOMY — Clean-from-Spec Source Candidate V1

**Identity:** `AI-COMPANY-AUTONOMY` / 2026-10-09 / ChatGPT offhost maker only.

This is a new **non-production source candidate**, derived from Owner/RIN CS0–CS9 requirements. It is NOT cloned from `Donkkub`, legacy HERMES runtime, quarantined scripts, or the v0.5 package. It is NOT a trusted LF4 source, approved workspace on Donkkub, independent THEMIS verification, or an agent execution system.

## Module mapping
- `company_core.py`: choose one deterministic eligible task, verified by an injected authority-checking interface (defaults deny).
- `durable_ledger.py`: SQLite synthetic transactional queue, fencing epoch, immutable receipt per project/task, exact replay, conditional lease expiry.
- `supervisor_mechanical.py`: pure wake-request planner, **never invokes RIN** or calls live tools.
- `agent_adapters.py`: fixed five profile names and permanently disabled live dispatch.
- `verifier.py`: explicit NOT_RUN until an independently bound THEMIS route exists.
- `project_isolation.py`: exact identity enforcement.
- `security.py`: LF3/LF4/LF5/A2 gates modeled as blocked; real execution **always denied**, including when flags are set.

## Local maker testing (on approved isolated workspace only)

`python -m unittest discover -s tests -v`

No network or external dependencies. Unit tests use synthetic fixtures and temp SQLite. **Do not run or extract on Donkkub during LF3 hold.** Avoid interpreting Python source text or a test-success message as a security approval.

## Missing before operational use
An authenticated issuer registry with external trust-root/key management and revocation proof; independent upstream/source provenance, frozen dependencies, genuine human endpoint acceptance (LF3), trusted writer/reader separation and backup-recovery (LF5), approved Hermes confinement (A2), real agent routes and credential scopes, real supervisor lifecycle, real multi-project acceptance, THEMIS independent verification. All are missing by design.

## Provenance classification
`CHATGPT_OFFHOST_MAKER_CANDIDATE_NOT_INDEPENDENTLY_VERIFIED`.
