# Architecture Handoff - Top-Level Streamlit Lazy Navigation v1

## Project

AI Health Coach / fitness_ai

## Branch

feature/top-level-streamlit-lazy-navigation-v1

## Milestone

Top-Level Streamlit Lazy Navigation v1

## Status

Implemented / ready for Architecture review after validation.

## Context

Developer Mode Linux Latency Investigation v1 proved `render_developer_section()` itself was fast. A later Linux timing capture showed the Developer section completing in milliseconds while top-level Workout and History tab bodies consumed roughly 30 seconds before Developer could render.

Root cause: Streamlit top-level `st.tabs` eagerly executes all tab bodies.

## Change

Replaced the top-level `st.tabs` block in `ui/streamlit_app.py` with radio-based selected-page navigation. The same top-level pages remain available, but only the selected page body executes per rerun.

## Boundaries

- No Weekly Coach Summary QA Date Range Debug v2 changes.
- No provider runtime changes.
- No Ollama/CrewAI/qwen calls.
- No worker/queue/scheduler/polling.
- No database schema changes.
- No raw provider/debug leakage.

## Acceptance request

Please review and accept as `TOP_LEVEL_STREAMLIT_LAZY_NAVIGATION_V1_ACCEPTED` if Linux Developer navigation no longer waits for Workout/History cold renders and normal page access remains intact.
