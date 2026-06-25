# Open Questions

## Daily Narrative feedback hardening

The first feedback-driven deterministic copy hardening pass is implemented. The next question is whether Architecture wants a second pass focused on provider-facing examples and validation prompt guidance, or whether Daily Narrative should pause while workout variety or Weekly Summary copy quality moves forward.

## Feedback storage lifecycle

The v1 feedback store is local JSONL and should not be committed by default. A future milestone may decide whether selected approved examples should be manually promoted from runtime feedback into project-memory docs. Raw runtime JSONL should not be committed.

## Provider usage

Provider candidates remain manual/debug-only. Before public provider display, the app needs enough approved examples and scenario-specific guidance to keep provider output from drifting into generic or awkward copy.

## Model selection

Do not treat bad Daily Narrative copy as a model-size issue yet. The current priority is richer context, better examples, adaptive deterministic fallback, and a feedback loop.

## Workout variety

Workout selection persistence is fixed. Exercise variety remains separate backlog work.
