# Architecture Principles

Last updated: 2026-06-18

## Core doctrine

Backend owns truth.

AI explains approved truth.

Validator enforces reality.

## Backend owns

- Calculations
- Targets
- Gaps
- Logged values
- Workout data
- Nutrition data
- Recovery status
- Training load
- Validation
- Persistence
- Deterministic fallback
- Approved claims

## AI/provider owns

- Explanation
- Synthesis
- Tone
- Coaching phrasing
- User-facing narrative

## Sectionized report architecture

The full report should not be owned by one monolithic model call. The preferred pattern is:

```text
section source data
→ derived evidence
→ approved claims
→ optional provider explanation
→ section validator
→ approved section
→ deterministic fallback
→ full report composition
→ safe persistence
```

## Safety boundaries

- Deterministic remains default.
- direct_ollama remains opt-in only.
- qwen3 remains experimental only.
- Provider output is never trusted by default.
- Raw provider output and raw CrewAI errors must not be public or persisted publicly.
- Validators should be tightened by evidence, not loosened for prettier copy.
