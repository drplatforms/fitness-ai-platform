# Current implementation update - Weekly Coach Summary Provider Runtime Design v1

Weekly Coach Summary Provider Runtime Design v1 is implemented on
`feature/weekly-coach-summary-provider-runtime-design-v1` after accepted commit
`be2f321 Add provider runtime resource lifecycle policy`.

This milestone is design-only. It documents the future direct_ollama +
qwen2.5:3b Weekly Coach Summary provider path against the existing bounded
WeeklyCoachSummaryContext seam. It also adds non-executing provider contract
models/tests so the future prototype has a concrete JSON shape and safety
boundary.

Current accepted foundations:

- runtime DB source diagnostics
- QA seed verification CLI
- top-level Streamlit lazy navigation
- Weekly Coach Summary QA Date Range Debug v2
- Weekly Coach Summary QA Data Context Integration v1
- Provider Runtime Resource Lifecycle Design v1

Live QA window:

- `2026-05-31` through `2026-06-06`
- happy path: user 102 `aligned_managed`
- low-data path: user 105 `data_quality_limited`

Provider boundary:

- backend facts only
- safe aggregate context only
- qwen2.5:3b future prototype only
- parser + validator gate required
- deterministic fallback always remains
- Provider Runtime Resource Lifecycle policy required
- no raw rows, raw provider output, prompts, scratchpad, or rejected output in
  user-facing display/persistence

No provider runtime execution is added in this milestone.
