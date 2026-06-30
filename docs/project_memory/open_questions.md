# Open Questions — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

## Active questions

1. Does Workout Set Intelligence v1 use completed planned workout executions only?
2. Does it avoid using unlinked manual `workout_sets` as planned-vs-actual evidence?
3. Are completion, effort, rep range, load, logging quality, and confidence indicators bounded to the allowed deterministic values?
4. Does `actual_rir - planned_rir_midpoint` correctly treat lower actual RIR as harder than planned and higher actual RIR as easier than planned?
5. Do missing actual reps, actual RIR, actual weight, skips, substitutions, and incomplete set logging lower confidence or add reason codes/limitations?
6. Does `coach_safe_summary` avoid forbidden training language and automatic progression/deload recommendations?
7. Does Daily Coach Intelligence Snapshot v2 include `workout_set_intelligence` while preserving Recovery Intelligence v1, Training Execution Summary, and Nutrition Trend Window evidence?
8. Does `foundation_layer_status` honestly report `workout_set_intelligence: implemented_v1` without pretending Trend Engine, Seed Data refinement, or Food Knowledge Expansion are complete?
9. Does the developer tool produce terminal-friendly workout set indicator artifacts for users 101-105 when QA seed data exists?
10. Does the snapshot avoid provider calls, DB mutation, Today UI changes, API/schema changes, and production behavior changes?
11. Is this source-data contract strong enough for Architecture to route Recovery Intelligence v2 next?

## Closed / carried-forward questions

Recovery Intelligence v1 was accepted as the first Backend Intelligence Foundation slice and remains read-only in this milestone.

Provider voice iteration remains paused after v4 and Fully Free Source-Data Lab evidence. Do not restart same-lane prompt/provider tuning from this milestone.

RAG, vector search, embeddings, and multi-agent orchestration remain parked behind Backend Intelligence Foundation layers.
