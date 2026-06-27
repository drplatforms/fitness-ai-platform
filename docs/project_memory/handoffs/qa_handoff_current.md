# QA Handoff Current — Daily Coach Narrative Value-Aware Provider Comparison v1

Milestone: Daily Coach Narrative Value-Aware Provider Comparison v1.

QA class: CLASS 2 / CLASS 5 HYBRID.

Status: backend implementation complete / ready for Architecture review.

## QA expectation

Focused backend/API/provider-contract smoke is recommended.

QA should validate:

- normal endpoint exists and hides runtime metadata;
- debug endpoint exists and exposes public-safe runtime metadata;
- deterministic provider remains default;
- direct_ollama is opt-in;
- openai is opt-in;
- exact-schema mocked provider output approves;
- extra-key provider output falls back;
- markdown-wrapped provider output falls back;
- missing OpenAI key falls back;
- provider exceptions/timeouts fall back;
- user 102 recovery parity case is protected;
- provider cannot claim `no recovery notes` when recovery signal/context exists;
- provider cannot say `without needing to address training or recovery`;
- provider cannot quote unapproved calorie targets or exact servings;
- no raw provider output, prompts, tracebacks, SQL, or debug internals leak into normal response;
- existing DailyCoachSynthesis behavior remains stable;
- existing nutrition actuals provenance debug endpoint remains stable.

## Suggested smoke routes

Normal endpoint:

`GET /daily-coach/102/narrative?date=2026-06-27`

Debug endpoint:

`GET /daily-coach/102/narrative/debug?date=2026-06-27`

## Not required

- full Streamlit workflow QA;
- full nutrition actuals QA;
- full workout/recovery/report QA;
- live provider calls in pytest.

## Scope confirmation

No normal Streamlit UI behavior changed.

No nutrition logging behavior changed.

No Target-vs-Actual totals changed.

No snapshots committed.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains the command-menu helper for port inspection.
