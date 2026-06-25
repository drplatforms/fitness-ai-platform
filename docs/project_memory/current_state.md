# Current State

Latest implemented milestone: Workout Exercise Variety Rotation v1.

Current branch: `feature/workout-exercise-variety-rotation-v1`.

Baseline: updated `main` after Daily Narrative Feedback-Driven Copy Rule Hardening v1 was accepted and closed out.

Workout preview generation now supports controlled deterministic exercise variation. The initial preview remains stable, normal Streamlit reruns do not regenerate exercises, and the user can explicitly request another unselected preview variation with `Show different exercises`.

The variation path is deterministic and bounded:

- `preview_variation_index = 0` is the initial preview
- explicit refresh increments the variation index
- variation participates in deterministic top-candidate selection
- recent-exercise penalties, equipment constraints, movement-pattern coverage, template intent, and workout validation remain in force

Selected workouts remain frozen. Selecting a preview persists the exact visible workout, and Active Workout loads the selected workout rather than regenerating a new plan. The refresh action is disabled after a workout is selected so it cannot silently mutate the selected or active workout.

Boundaries remain: deterministic workout generation only, no AI/provider workout generation, no CrewAI/Ollama/OpenAI/PydanticAI/LangGraph work, no worker/queue/scheduler/polling, no selected workout mutation, no Today duplicate workout flow, no Daily Narrative regression, and no Weekly Summary behavior change.
