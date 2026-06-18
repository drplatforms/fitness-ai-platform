# Direct Ollama Training Report Section — Bounded Coaching Claims v1.1

## Status

Patch milestone for the Direct Ollama training report section spike.

## Purpose

Bounded Coaching Claims v1 gave the model more backend-approved single-session facts so the coach could sound less mechanical without inventing broad conclusions.

Runtime QA showed two narrow follow-up issues:

1. qwen2.5:3b could generate safe language while omitting an approved workout or exercise name from `limitations_context`.
2. qwen3:8b could turn an approved same-rep pattern into unsupported language such as “consistent effort across multiple lifts” or “focused work.”

v1.1 keeps validation strict and tightens the prompt so these failures are less likely.

## Scope

This patch:

- Requires the prompt to tell the model that `limitations_context` must mention the approved workout name or an approved exercise name.
- Clarifies that same-rep language may only describe the same rep count across logged sets inside the workout/session.
- Clarifies that RIR-based effort language may only describe logged RIR inside the workout/session.
- Explicitly tells the model not to translate same-rep language into consistent effort, consistent performance, or focused work.
- Keeps qwen3-style broad consistency/effort language rejected.
- Removes an unused local variable flagged by Ruff.

## Non-goals

This patch does not:

- Loosen validation.
- Add new broad allowed claims.
- Make qwen3 the default.
- Wire training report sections into full reports or Streamlit.
- Add more phrase bans as the main product strategy.
- Change the direct_ollama provider default.

## Target behavior

Allowed when supported by approved bounded claims:

- “same rep count across the logged sets”
- “steady reps in this session”
- “close to failure based on the logged RIR”
- “single-session reference point”

Still rejected:

- “consistent effort across multiple lifts”
- “focused work”
- “consistent performance over time”
- “progression confirmed”
- “recovery looks good”
- “strong execution”

## Runtime QA interpretation

A safe candidate that fails only because `limitations_context` lacks an approved name should be treated as a prompt/anchoring issue, not a safety failure.

A qwen3 candidate that says “consistent effort” or “focused work” should stay rejected because those phrases over-expand the approved bounded claims.
