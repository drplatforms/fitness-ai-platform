# Current implementation update - Weekly Coach Summary Provider Runtime Prototype v1

Weekly Coach Summary Provider Runtime Prototype v1 is implemented on
`feature/weekly-coach-summary-provider-runtime-prototype-v1` after accepted commit
`f13e784 Design weekly coach summary provider runtime`.

This is the first controlled Developer Mode-only manual provider prototype for
Weekly Coach Summary. The provider path uses the accepted backend-owned selected
QA date-range context seam and accepted Provider Runtime Resource Lifecycle
policy.

Implemented behavior:

- qwen2.5:3b is the only approved prototype model
- provider preview is Developer Mode-only
- provider preview is manual-button-only
- no provider call happens on page open
- no provider call happens when only building context
- provider input is built by backend service, not Streamlit
- provider receives only bounded safe aggregate context and deterministic baseline
- parser requires JSON-only output
- validator rejects unsupported, unsafe, overconfident, raw, or ungrounded output
- deterministic fallback remains authoritative on failure
- lifecycle keep_alive/unload policy is applied
- normal/default UI remains unchanged

Live QA window remains `2026-05-31` through `2026-06-06`.

Still deferred:

- public/default Weekly Coach Summary display
- normal Today Weekly Coach Summary display
- automatic generation
- worker / queue / scheduler / polling
- CrewAI
- qwen3 / qwen3:32b promotion
