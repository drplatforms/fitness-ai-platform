# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Latest implemented feature branch milestone: Daily Narrative QA Date Range Preview / Grounding v1.

Key rule: backend tells the truth; provider improves voice; validator decides what survives; deterministic fallback always works.

Daily Narrative now has a Developer Mode-only QA seeded date/date-range preview seam. Use QA users 101-105 and the verified seeded window `2026-05-31` through `2026-06-06` for smoke testing. The preview context uses safe aggregate facts and missing-data reasons only. Normal Today behavior is unchanged.

Previous accepted provider milestone: Weekly Coach Summary Provider Runtime Prototype v1 (`c0f7a84`).

## Workout Plan Selection Persistence + Today Workout De-dup v1

Current authorized hotfix: fix Workout preview -> Select This Workout -> Active Workout persistence and remove the duplicate full workout selection flow from Today. Workout page is canonical for Plan / Active / Review. Today shows only compact workout status and route-to-Workout behavior.

Boundaries: no provider/AI workout generation, no CrewAI/Ollama changes, no automatic generation, no worker/queue/scheduler/polling, no exercise variety/rotation work, no Streamlit theme cleanup.
