# Weekly Coach Summary Persistence Latency Investigation v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: `WEEKLY_COACH_SUMMARY_PERSISTENCE_LATENCY_INVESTIGATION_V1_ACCEPTED`

## Purpose

Investigate the unacceptable 26 to 35 second latency observed in the Weekly Coach Summary Developer Mode persistence flow and apply the smallest safe fix.

## Root cause

The core deterministic Weekly Coach Summary service and SQLite persistence path are fixture-sized backend operations. The observed latency was strongly narrowed to Streamlit full-app rerun behavior: button clicks inside the Developer tab reran the entire multi-tab app body, causing unrelated Today, Workout, Nutrition, History, and Reports rendering work to dominate perceived latency.

## Fix

The Weekly Coach Summary Developer Mode inspection panel now uses Streamlit fragment reruns when `st.fragment` is available. This isolates Weekly Coach Summary button interactions so generate/save/load actions rerun only the panel instead of the entire app.

The fix also adds Developer Mode-only timing diagnostics and a CLI latency probe:

- `tools/dev_weekly_coach_summary_latency_probe.py`
- Developer Mode-only `Weekly Coach Summary Timing`

## Before timing

Manual smoke before this milestone observed:

- deterministic weekly summary generation: approximately 30 seconds
- save/load interaction: approximately 26 to 35 seconds

## Expected after timing

Target after the fragment fix:

- deterministic service generation: under 1 second
- SQLite save/load: under 1 second each
- Developer Mode generate/save/load perceived latency: under 3 seconds on supported Streamlit versions

## Boundaries

- Developer Mode-only timing diagnostics
- no public/default display
- no normal Today integration
- no provider runtime
- no Ollama/CrewAI/qwen calls
- no worker/queue/scheduler/polling
- no automatic weekly generation
- no persistence safety rule changes
- no raw provider output persistence/display
- no rejected provider output persistence/display
- no prompt/raw context/scratchpad persistence/display
- no Codex used
