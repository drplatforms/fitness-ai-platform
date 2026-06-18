# Backend Truth Contract

Last updated: 2026-06-18

The backend truth contract defines what the backend must own before AI can explain it.

## Truth sources

A claim can be user-facing only when it comes from one of these backend-owned sources:

- Stored user profile or health state.
- Logged workouts, sets, reps, loads, RIR, and dates.
- Logged nutrition entries and canonical food references.
- Approved nutrition target calculations and display flags.
- Recovery/check-in state.
- Derived evidence service output.
- Approved claim service output.
- Validated deterministic fallback.

## Claims AI must not invent

AI/provider must not invent:

- Progression over time.
- Consistency over time.
- Fatigue or recovery interpretation.
- Form/control claims.
- Adherence.
- Planned-work alignment.
- Completion claims.
- Calorie targets.
- Protein targets.
- Medical claims.
- Supplement recommendations.
- Deficiencies.
- Severe deficit claims.
- Body-composition conclusions.

These claims are allowed only when the backend explicitly approves them through evidence and claim services.

## Public persistence rule

Public report history should contain only user-safe report content and allowlisted metadata. Raw prompts, raw provider payloads, parser internals, validator internals, tracebacks, and exception text must not be persisted publicly.
