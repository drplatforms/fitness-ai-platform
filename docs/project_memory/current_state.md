# Current State

Latest implemented milestone: Exercise Catalog Utilization / Specialized Movement Coverage v1.

Current branch: `feature/exercise-catalog-utilization-specialized-movement-coverage-v1`.

Baseline: updated `main` after Workout Exercise Variety Rotation v1 was accepted and closed out.

Workout Exercise Variety Rotation v1 is accepted and merged. The app now supports stable workout previews, explicit `Show different exercises` preview refresh, frozen selected workouts, stable Active Workout loading, and Today workout de-duplication.

This milestone builds on that accepted behavior by broadening deterministic workout candidate pools with same-pattern, equipment-compatible catalog alternatives. The workout templates still define slot intent, but each slot can now reach more of the existing exercise catalog when safe alternatives exist.

Implemented behavior:

- template slots remain deterministic and movement-pattern anchored
- catalog-backed alternatives are added only when they match slot movement patterns
- available/unavailable equipment filtering still applies
- avoided movement constraints still apply
- data-quality-limited workouts stay simple and do not expand into harder specialized choices
- preview variation can reach more specialized movements where suitable alternatives exist
- selected workout immutability remains preserved
- Active Workout behavior remains preserved
- Today workout de-dup remains preserved
- no provider/AI workout generation was introduced

A diagnostic catalog utilization report helper now summarizes:

- total catalog exercises
- equipment-eligible exercise count
- movement-pattern eligible count
- requested/available/missing movement patterns
- movement-pattern counts and examples

Boundaries remain: deterministic workout generation only, no AI/provider workout generation, no CrewAI/Ollama/OpenAI/PydanticAI/LangGraph work, no worker/queue/scheduler/polling, no selected workout mutation, no Today duplicate workout flow, no Daily Narrative regression, and no Weekly Summary behavior change.
