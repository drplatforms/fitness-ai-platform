# Open Questions

## Daily Narrative voice quality

Daily Narrative context differentiation should be proven before model escalation. Once rich-day, low-data, and no-data contexts clearly differ, the next question is whether qwen2.5:3b can produce acceptable voice or whether qwen3:8b should be a controlled candidate under strict lifecycle policy.

## Rich seeded day availability

The rich-day scan should be run against the active Linux runtime DB. If user 102 does not have a useful rich day in the expected window, the issue is seed coverage rather than model quality.

## Public display

No public/default Daily Narrative provider display is approved yet. Normal Today behavior remains deterministic-first.

## Workout Plan Selection Persistence + Today Workout De-dup v1

Current authorized hotfix: fix Workout preview -> Select This Workout -> Active Workout persistence and remove the duplicate full workout selection flow from Today. Workout page is canonical for Plan / Active / Review. Today shows only compact workout status and route-to-Workout behavior.

Boundaries: no provider/AI workout generation, no CrewAI/Ollama changes, no automatic generation, no worker/queue/scheduler/polling, no exercise variety/rotation work, no Streamlit theme cleanup.
