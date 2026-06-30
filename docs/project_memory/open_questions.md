# Open Questions — Daily Coach Intelligence Snapshot + Recovery Intelligence v1

## Active questions

1. Does Recovery Intelligence v1 correctly use `checkin_date` as the primary date and only use `created_at`/`id` for duplicate same-day resolution?
2. Do duplicate same-day check-ins get deduped without distorting recovery averages?
3. Are sleep, energy, soreness, readiness, fatigue risk, trend direction, and confidence labels bounded to the allowed deterministic values?
4. Does the Daily Coach Intelligence Snapshot include Recovery Intelligence plus read-only existing Training Execution Summary and Nutrition Trend Window evidence?
5. Is `foundation_layer_status` explicit that only Recovery Intelligence is implemented v1 while other foundation layers remain partial/existing-only/pending?
6. Does the developer tool produce terminal-friendly artifacts for users 101-105 when QA seed data exists?
7. Does the snapshot avoid provider calls, DB mutation, Today UI changes, API/schema changes, and production behavior changes?
8. Is this source-data contract strong enough for Architecture to route the next Backend Intelligence slice?

## Closed / carried-forward questions

Provider voice iteration remains paused after v4 and Fully Free Source-Data Lab evidence. Do not restart same-lane prompt/provider tuning from this milestone.

RAG, vector search, embeddings, and multi-agent orchestration remain parked behind Backend Intelligence Foundation layers.
