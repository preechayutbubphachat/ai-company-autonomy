# V1 source integrity and independent verification handoff

Project: `AI-COMPANY-AUTONOMY`
Immutable subject commit: `05afc1c4fb171221ff755f6bfb3dc93710f87301`
Candidate branch: `candidate/clean-source-v1-20261009`
Review branch: `review/v1-source-integrity-20261009`

## Source of truth
Private GitHub repository `preechayutbubphachat/ai-company-autonomy`. Compare against **immutable subject SHA**, never a moving branch. The source manifest claims 13 members, but maker-side reports are not independent verification.

## Execution sequence (no micro-approvals within read-only review)
1. RIN: reconcile project identity and the frozen subject SHA; read repository permissions and state using an actually available authorized route. Do not claim RIN has GitHub access merely because ChatGPT does.
2. Independent reviewer THEMIS: using a separately evidenced read-only route, fetch exact subject, compute SHA-256/size of all 13 manifest members, check manifest accuracy, inspect code and imports, and run tests in an approved offhost isolated workspace. Record interpreter version, commands, raw output and source revision.
3. Check `company_v1` for actual runtime behavior: deny-by-default authorization, project scoping, SQLite lease fencing/replay, exact five profiles, no live dispatch, no actual supervisor or agent integration. Report deficiencies, not just tests.
4. Compare to the earlier ZIP identity `bdac473954f311ca767dbbf7043775ae1ff21b58160d962074f9f3fb2bad26c1`; if bytes differ, label `SOURCE_DRIFT` and require a new reviewed manifest. Never assume a matching filename proves matching content.
5. HERMES maker may propose bounded fixes on a separate fix branch **only after writer route and scope are verified**; do not silently overwrite the frozen subject.
6. RIN adjudicates with independent receipts bound to exact revision; do not promote LF4 from maker tests alone.

## Current boundary
`LF3=BLOCKED`, `LF4=UNVERIFIED`, `LF5=NOT_PROVEN`, `A2=BLOCKED_FORMALLY_PARKED_AT_C0`. No host mutation, Donkkub extraction, CI, merge, deploy, secrets, production source promotion or live agent dispatch.

## Acceptance
Return: subject SHA, manifest mismatch count, independent test count and failure details, reviewer identity/route proof, blocker classification, and highest-impact next action toward `AUTONOMOUS_MULTI_PROJECT_AI_COMPANY_OPERATIONAL`. If independent route is unavailable, report `INDEPENDENT_REVIEW_ROUTE_BLOCKED` once; do not repeat synthetic loops.
