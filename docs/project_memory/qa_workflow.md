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

## Real-path quality gates

QA validates the actual user path, not only generic test status.

For complex milestones, QA should distinguish:

- targeted validation green,
- regression tests green,
- browser smoke green,
- Linux smoke green,
- accepted product behavior.

When smoke fails, QA should ask whether the failed path is represented in an automated regression test, diagnostic/coverage test, documented limitation, or backlog item.

Every major smoke failure should become one of those four outcomes. It should not remain tribal knowledge.

QA should treat browser smoke and Linux smoke failures as process signals. If Windows validation is green but Linux smoke fails, the branch is not acceptance-ready.
