# Product Vision

Last updated: 2026-06-20

## North star

AI Health Coach is a local-first, validation-first coaching platform that helps the user make better daily nutrition, workout, recovery, and planning decisions without letting an LLM invent truth.

The desired product eventually feels like a real coach: informed by verified user data, aware of trends and constraints, proactive but not reckless, personal but not hallucinated, useful every day, and transparent enough to debug.

## Product doctrine

Backend owns facts. AI explains facts.

The product should feel premium, but never fake precision or unsupported certainty.

## Current product loop

The current accepted loop includes daily deterministic next action, deterministic Today Coach Note, deterministic Coach's Read / Daily Coach Synthesis, grounded daily recommendation, nutrition logging and target-vs-actual context, workout planning/substitution/count/lifecycle cleanup, full reports with provider-integrated Training and Nutrition sections, and Developer Mode diagnostics for provider experimentation.

## Provider vision

The long-term provider vision is not a chatbot bolted onto a tracker.

The provider should eventually improve narrative quality, explanation quality, synthesis, tone, coaching feel, and prioritization explanation.

The provider should not own calculations, decisions, targets, workouts, catalogs, persistence, or truth.

`qwen3:32b` remains a possible future premium coach voice lane, not a promoted/default model.

## Future architecture themes

Future ideas are captured in `docs/project_memory/future_architecture_ledger.md`:

- async validated provider narrative
- unified health state snapshots
- long-term inspectable coach memory
- curated RAG / knowledge base
- vector search over verified data
- explicit MoE/model routing
- MCP/tool interfaces through backend authority
- better frontend and local deployment

These ideas are recorded, not authorized.

## Product quality priorities

Near-term priorities:

1. keep project memory accurate
2. keep deterministic daily product loop stable
3. make provider preview contracts reliable
4. retry same-session approved narrative only when preview reliability is proven
5. keep improving workout/nutrition usability without breaking safety boundaries
6. clean global visual theme without changing product logic
