# QA Workflow

Last updated: 2026-06-18

## Testing doctrine

Tests should prove boundaries, not just happy paths.

For provider-related work, tests must prove:

- Deterministic remains default.
- Provider remains opt-in.
- No live Ollama calls occur in pytest.
- Raw provider output is not public.
- Raw CrewAI error text is not public.
- Fallback behavior is explicit and safe.

## Runtime QA doctrine

Runtime QA is used when async jobs, provider integration, persistence, or report composition behavior is changed or needs confirmation.

Common runtime checks:

- Job completes.
- Provider attempted status matches expected config.
- Selected provider/model are correct.
- Section source is correct.
- Persisted row exists.
- Report date is correct.
- Safe metadata keys exist.
- Raw/debug leakage is absent.

## No live provider in pytest

Ollama/direct provider calls belong in explicit runtime QA, not automated pytest.
