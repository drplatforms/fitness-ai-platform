# Weekly Coach Summary Date-Range QA Data Debug v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW
Proposed final status: WEEKLY_COACH_SUMMARY_DATE_RANGE_QA_DATA_DEBUG_V1_ACCEPTED

## Purpose

Add Developer Mode-only QA user/date-range debugging for Weekly Coach Summary so the deterministic path can inspect live seeded QA data through sanitized counts and aggregates.

## Scope

Implemented:

- read-only QA fact inventory service
- QA user selector support for users 101-105
- selected date range support
- safe date bounds and fact-count inventory
- deterministic summary context built from selected QA range counts
- Developer Mode-only QA data range controls
- selected-range generate/save/load behavior
- persistence isolation by selected user/date range
- tests and project memory updates

## Boundaries

No public/default Weekly Coach Summary display is authorized.
No normal Today Weekly Coach Summary display is authorized.
No provider runtime is authorized.
No Ollama/CrewAI/qwen calls are authorized.
No automatic generation, worker, queue, scheduler, polling, or background process is authorized.
Raw rows, raw notes, raw food logs, raw workout set rows, provider output, prompts, raw context, scratchpad, and chain-of-thought remain forbidden.

## Validation

Run focused model, service, persistence, QA data service, Streamlit source/structure, project memory, preview, latency probe, py_compile, and fsweep checks.
