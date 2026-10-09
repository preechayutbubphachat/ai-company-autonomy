# Security boundary
- No Windows host mutation, process control, scheduled tasks, registry, Defender, credentials, network, or live providers.
- `DenyAllVerifier` is used by default. `TestOnlyVerifier` must never authorize live work.
- Every API marked `_test_only` is a development-fixture API, not a production task-execution service.
- The host cannot be certified based on this artifact. THEMiS and qualified human reviewer are separate.
- No company GitHub repo was created, no commit/PR/CI and no child project touched.
- No demo signing secrets shipped. No production authorization mechanism is implemented.
