# Workout Preview Full-Slot Rotation v1

Status: IMPLEMENTATION IN PROGRESS

Branch: `feature/workout-preview-full-slot-rotation-v1`

Source baseline: current `main` after Workout Generation Sizing + Persistence Stabilization v1 acceptance.

Goal: improve explicit workout preview refresh variety so each overlapping slot attempts to use a different valid exercise when safe same-pattern/equipment alternatives exist.

Scope:

- Preserve Quick / Standard / Full range behavior.
- Preserve selected workout immutability.
- Preserve Active Workout persistence.
- Preserve Today workout de-duplication.
- Improve deterministic slot-level rotation for refreshed previews.
- Preserve Internal Rotation / External Rotation validation behavior.

Non-goals:

- no broad 200+ exercise catalog utilization
- no selected-workout replacement flow
- no AI/provider workout generation
- no Ollama/CrewAI/OpenAI/PydanticAI/LangGraph
- no worker/queue/scheduler/polling
- no latency optimization
- no Daily Narrative or Weekly Summary changes
