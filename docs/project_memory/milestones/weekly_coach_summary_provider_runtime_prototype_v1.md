# Weekly Coach Summary Provider Runtime Prototype v1

Status: Implemented / ready for Architecture review

Branch: `feature/weekly-coach-summary-provider-runtime-prototype-v1`

This milestone implements the first Developer Mode-only manual provider preview for Weekly Coach Summary.

## Scope

Implemented:

- backend provider service using bounded `WeeklyCoachSummaryContext`
- direct Ollama request path for `qwen2.5:3b`
- strict JSON-only provider candidate parsing
- validator for grounding, safety, low-data confidence, and unsupported progression claims
- deterministic fallback for provider disabled, unreachable, timeout/error, invalid JSON, validation failure, and insufficient context
- Developer Mode-only manual preview controls inside Weekly Coach Summary QA Date Range Debug
- lifecycle policy integration through `keep_alive` and automatic unload-after-request handling
- fake-transport tests; automated tests do not require live Ollama
- optional dry-run/live CLI smoke helper

Not implemented:

- public/default Weekly Coach Summary display
- normal Today display
- automatic generation
- worker / queue / scheduler / polling
- CrewAI
- qwen3 or qwen3:32b
- raw provider output display/persistence
- rejected provider output persistence

## Runtime boundary

Provider preview is manual-button-only and Developer Mode-only. Normal deterministic paths work without Ollama or provider env vars.

The approved prototype model is `qwen2.5:3b` only. The request includes lifecycle `keep_alive` from the accepted provider lifecycle policy. Default local behavior is conservative and requests unload with `keep_alive=0`.

## Manual smoke

Use the live QA window:

- user 102: `2026-05-31` through `2026-06-06`
- user 105: `2026-05-31` through `2026-06-06`

The UI provider preview remains disabled until `FITNESS_AI_WEEKLY_SUMMARY_PROVIDER_PREVIEW_ENABLED=true` is set in the runtime environment.
