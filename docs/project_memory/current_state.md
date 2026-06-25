# Current State

Latest implemented milestone: Daily Narrative Feedback-Driven Copy Rule Hardening v1.

Current branch: `feature/daily-narrative-feedback-driven-copy-rule-hardening-v1`.

Baseline: `main` at `644792d` after Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1 was accepted and merged.

Daily Narrative now has a Developer Mode-only Voice Lab with synthetic safe scenario fixtures, deterministic candidates, style checks, local bad / better / approved feedback capture, and feedback-driven copy hardening. The feedback-capture milestone made user examples available; this milestone applies the first captured feedback into deterministic copy families, copy-quality checks, provider-facing voice examples, and scenario-specific guidance.

Current hardening targets applied:

- replace `before you treat the plan as automatic` with direct recovery-based intensity planning
- replace `adding random data` with full-day review language
- replace high-soreness lower-body phrasing that says `let how you move decide whether the session stays heavy`
- improve rich all-domain day language without claiming `optimal results`
- improve mixed-signals language without unsupported `does not support expended energy` physiology claims

Daily Narrative voice target remains: practical coach, grounded in facts, slightly technical where helpful, not a debug panel, not a compliance memo, not a washer hardware manual, and not obviously AI-written.

Feedback persistence remains local and safe by default. Runtime feedback records must not include raw food logs, raw workout rows, raw check-in notes, raw set rows, prompts, scratchpad, chain-of-thought, or secrets. Runtime feedback files such as `artifacts/daily_narrative_feedback.jsonl` must remain local and unstaged.

Boundaries remain: no model promotion, no public/default provider display, no automatic generation, no worker/queue/scheduler/polling, no CrewAI reintroduction, no raw rows/logs/notes/set rows exposure, and no Streamlit theme cleanup.
