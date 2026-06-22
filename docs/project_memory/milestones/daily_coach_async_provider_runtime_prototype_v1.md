# Daily Coach Async Provider Runtime Prototype v1 — Developer Mode Only

Status: AUTHORIZED FOR BACKEND / STREAMLIT IMPLEMENTATION

Branch: `feature/daily-coach-async-provider-runtime-prototype-v1`

Source baseline: `df088f9 Merge developer mode persistence inspection closeout`

Goal: implement a Developer Mode-only manual provider runtime prototype that can run one explicitly triggered provider attempt for a persisted Daily Coach async job, parse strict JSON, validate safety, persist approved public-safe narrative output only, or persist sanitized failure/fallback metadata only.

In scope:

- Developer Mode-only manual provider trigger
- provider runtime disabled by default
- `DAILY_COACH_ASYNC_PROVIDER_RUNTIME_ENABLED` gating
- `DAILY_COACH_ASYNC_PROVIDER=direct_ollama` for the prototype
- `DAILY_COACH_ASYNC_PROVIDER_MODEL=qwen2.5:3b` bridge baseline only
- strict provider input from backend-approved context only
- strict JSON parser and Daily Coach narrative validator
- approved public-safe narrative persistence after validation
- sanitized failure/fallback metadata only
- Developer Persistence Inspection used to inspect result state

Non-goals:

- no normal Today provider call
- no public async narrative display
- no provider call on page load
- no automatic async job creation outside manual Developer Mode action
- no worker / queue / scheduler / polling
- no qwen3 bridge
- no qwen3 promotion
- no qwen3:32b promotion
- no raw provider output persistence
- no rejected provider output persistence
- no full prompt/raw context/scratchpad persistence
- no debug/provider metadata in normal UI
- no Codex by default

Validation plan:

- provider runtime prototype tests
- Streamlit Developer Mode provider panel tests
- Developer Mode persistence inspection tests
- persistence service shell tests
- schema/contracts tests
- async narrative contract tests
- project-memory checks
- focused ruff/black/py_compile
- manual Streamlit smoke after Linux pull

Expected final status:

`DAILY_COACH_ASYNC_PROVIDER_RUNTIME_PROTOTYPE_V1_ACCEPTED`
