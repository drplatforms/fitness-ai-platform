# Public Screenshot Capture Checklist

Status: STREAMLIT_PORTFOLIO_VISUALIZATION_POLISH_V4_READY_FOR_QA candidate

Branch: chore/public-ui-polish

Primary demo user: QA 102 — Well-recovered baseline
Secondary demo user: QA 105 — Messy/incomplete logging

## Validation before screenshots

- `ruff check . --fix`
- `black .`
- `python -m py_compile ui/streamlit_app.py`
- `pytest tests/test_full_report_section_registry.py -q`
- `pytest tests/test_report_persistence_boundary.py -q`
- If anything beyond Streamlit/docs changed: `scripts/dev_commit_check.ps1 -Mode code`

## Required visualization-ready screenshot candidates

1. User 102 Today / Daily Coach Overview
2. User 102 Nutrition Target Band / Target-vs-Actual
3. User 102 Quick Log Food / Food Suggestion Cards
4. User 102 Workout Preview Card Layout
5. User 102 Nutrition Report Section
6. Terminal validation passing

## Optional screenshots

7. User 105 limited-confidence / safety-boundary nutrition view
8. User 105 sanitized Developer Debug Metadata view
9. User 101 recovery-limited coaching boundary view

## Capture rules

- Use seeded data.
- Keep Developer Mode off unless intentionally capturing engineering evidence.
- Do not capture raw provider output, prompt text, schema text, exception internals, or tracebacks.
- Normal UI screenshots should show user value first.
- Engineering screenshots should show sanitized metadata only.
- Avoid local paths unless capturing terminal validation.
- Avoid huge raw tables and unexpanded debug JSON.
- Keep direct_ollama described as opt-in/experimental where visible; do not present it as default.
- Do not show qwen3 as approved.
- Let Streamlit finish rerendering before capture.
- Move the cursor away from headings to avoid hover/link icons.

## Visualization-specific checks

- Nutrition target bands use approved Target-vs-Actual data only.
- Limited targets remain hidden and do not become numeric goals.
- Food suggestion cards show only backend-approved canonical foods, serving grams, and nutrient estimates.
- Workout preview cards use only the existing approved workout plan preview response.
- Normal UI does not expose provider/runtime metadata.

## Recommended capture order

1. Today tab, QA 102, Daily Grounded Recommendation expanded.
2. Nutrition tab, QA 102, target bands plus Target-vs-Actual table.
3. Nutrition tab, QA 102, Quick Log Food flow or Food Suggestions cards.
4. Workout tab, QA 102, Plan step with Workout Preview Card Layout.
5. Reports tab, QA 102, latest sectionized Nutrition or Training report section.
6. Terminal validation screenshot after checks pass.

## Final acceptance label

STREAMLIT_PORTFOLIO_VISUALIZATION_POLISH_V4_READY_FOR_QA


## Portfolio visual tightening v3 notes

- Target band cards should be compact enough for a single screenshot.
- Food suggestion cards should use color chips but remain optional, not meal-plan language.
- Workout preview cards should avoid oversized metric blocks.
- Today page should make Recovery Check-In visible as the first coaching input.
- Developer Mode should remain off for normal screenshots.

## Canonical quick-log v4 notes

- Nutrition should lead with a clear quick-log flow: search, select, grams, log.
- Canonical food matches should support the logging action instead of dominating the page.
- Existing source-food search remains available only as an advanced fallback.
- Garnet/gold accents are visual-only and do not change product behavior.
