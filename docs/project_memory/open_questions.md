# Open Questions

## Daily Narrative feedback hardening

The Voice Lab can now capture bad/better/approved feedback. The next question is how aggressively future milestones should turn saved examples into deterministic copy rules and provider prompt examples.

## Feedback storage lifecycle

The v1 feedback store is local JSONL and should not be committed by default. A future milestone may decide whether selected approved examples should be promoted from runtime feedback into project-memory docs.

## Provider usage

Provider candidates remain manual/debug-only. Before public provider display, the app needs enough approved examples and scenario-specific guidance to keep provider output from drifting into generic or awkward copy.

## Model selection

Do not treat bad Daily Narrative copy as a model-size issue yet. The current priority is richer context, better examples, adaptive deterministic fallback, and a feedback loop.

## Workout variety

Workout selection persistence is fixed. Exercise variety remains separate backlog work.
