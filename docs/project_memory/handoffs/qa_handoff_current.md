# QA Handoff Current — Nutrition Actuals Provenance Debug / Integration Design v1

Milestone: Nutrition Actuals Provenance Debug / Integration Design v1.

QA class: CLASS 2 / CLASS 3 HYBRID.

Status: backend implementation complete / ready for Architecture review.

## QA expectation

Focused backend/API/debug contract and semantics smoke is recommended.

QA should validate:

- endpoint exists;
- valid user/date returns public-safe interpretations;
- serving-unit actuals show provenance/confidence;
- ranged estimates surface range metadata;
- missing nutrients stay missing/unknown, not zero;
- empty day returns safe response;
- invalid date returns safe error;
- no raw/debug/source/provider leakage;
- existing logging paths stable;
- Target-vs-Actual totals unchanged;
- no Streamlit behavior change;
- no AI/provider behavior change.

## Not required

- full Streamlit workflow QA;
- full AI/provider QA;
- full workout/recovery/report QA.

## Suggested smoke route

`GET /nutrition/{user_id}/actuals-confidence/debug?date=YYYY-MM-DD`

## Scope confirmation

No normal user UI behavior changed.

No nutrition logging behavior changed.

No Target-vs-Actual totals changed.

No snapshots committed.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains the command-menu helper for port inspection.
