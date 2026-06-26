# Current State

Latest accepted milestone: Workout Generation Sizing + Persistence Stabilization v1.

Current implementation milestone: Workout Preview Full-Slot Rotation v1.

Current branch: `feature/workout-preview-full-slot-rotation-v1`.

Source baseline: current `main` after Workout Generation Sizing + Persistence Stabilization v1 acceptance. The paused branch `feature/exercise-catalog-utilization-specialized-movement-coverage-v1` remains a checkpoint/reference only and must not be merged or patched further.

This milestone improves preview variety while preserving the stabilized workout generation contract:

- Quick / Standard / Full remain size ranges, not fixed constants.
- Quick targets 3-4 exercises when valid.
- Standard targets 4-5 exercises when valid.
- Full targets 6-7 exercises when valid.
- Same inputs plus the same preview variation key produce the same preview.
- A different preview variation key may choose a different valid plan/count within the selected range.
- `Show different exercises` affects only unselected previews and attempts to rotate every overlapping exercise slot when safe same-pattern/equipment alternatives exist.
- Selected and Active Workout rendering comes from persisted selected/active state, not preview generation.
- Selecting a preview persists the exact visible workout.
- Valid exercise names such as Cable Internal Rotation and Cable External Rotation do not trip internal/debug copy validation.

Boundaries remain: deterministic workout generation only, no broad 200+ exercise catalog utilization, no AI/provider workout generation, no CrewAI/Ollama/OpenAI/PydanticAI/LangGraph work, no worker/queue/scheduler/polling, no selected workout replacement flow, no Daily Narrative change, no Weekly Summary change, no latency optimization in this milestone, no snapshots/qa_artifacts/patch files committed.
