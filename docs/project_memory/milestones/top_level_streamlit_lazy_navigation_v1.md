# Top-Level Streamlit Lazy Navigation v1

## Status

Implemented for Architecture/QA review.

## Problem

Streamlit `st.tabs` eagerly executes every top-level tab body on each rerun. On the Linux runtime, opening Developer Mode could wait for the Workout and History sections to complete cold renders before the Developer section rendered. Timing showed the Developer section itself completed in milliseconds, while earlier tab bodies consumed most of the latency.

## Decision

Replace only the top-level `st.tabs` navigation with radio-based selected-page navigation so one top-level page body executes per rerun.

## Scope

- `ui/streamlit_app.py` top-level navigation only.
- Preserve Today, Workout, Nutrition, History, Reports, and Developer sections.
- Preserve Developer Mode timing instrumentation.
- Add source-level regression tests proving top-level navigation is lazy.
- Update project memory docs and handoffs.

## Non-goals

- No Weekly Coach Summary QA Date Range Debug hardening.
- No provider runtime.
- No Ollama, CrewAI, or qwen calls.
- No queue, scheduler, worker, polling, or automatic generation.
- No broad Streamlit rewrite.
- No database schema change.
- No raw row/debug/provider leakage.

## Acceptance expectations

- Selecting Developer renders Developer without first rendering Workout/History/Nutrition.
- Linux Developer navigation latency is materially improved.
- Normal page content remains reachable from the new top-level navigation.
- Existing Developer Mode diagnostics remain button-driven.
- Existing tests and project-memory checks pass.
