# QA Handoff - Top-Level Streamlit Lazy Navigation v1

## QA focus

Validate Linux runtime navigation latency and confirm normal pages remain reachable.

## Smoke checklist

- Open app on Linux runtime.
- Select Developer from top-level navigation.
- Confirm Developer opens without waiting for Workout/History cold renders.
- Confirm Today, Workout, Nutrition, History, Reports, and Developer are all reachable.
- Confirm Runtime / DB Source Verification remains button-driven.
- Confirm no provider/Ollama/CrewAI/qwen calls.
