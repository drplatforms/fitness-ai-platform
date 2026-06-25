# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Latest implemented feature branch milestone: Daily Narrative Feedback-Driven Copy Rule Hardening v1.

Canonical baseline before this feature: `main` at `644792d`, after Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1 was accepted and merged.

Key rule: backend tells the truth; provider improves voice; validator decides what survives; deterministic fallback always works.

Daily Narrative now has a Developer Mode-only Voice Lab with synthetic scenario fixtures, local feedback capture, and feedback-driven deterministic copy hardening. Users can mark generated copy as bad, better, or approved; save rejected phrases; save preferred rewrites; and preserve scenario/candidate/reason-code context. The hardened copy rules now use the first captured feedback to improve rich-day, recovery-planned, high-soreness lower-body, and mixed-signals scenarios.

Current feedback storage: local JSONL via `artifacts/daily_narrative_feedback.jsonl` by default, or `DAILY_NARRATIVE_FEEDBACK_PATH` when configured. Runtime feedback files are not intended to be committed.

Daily Narrative voice target: practical coach, grounded in facts, slightly technical where helpful, not a debug panel, not a compliance memo, not a washer hardware manual, not obviously AI-written, and not overconfident.

Boundaries: no public/default Daily Narrative provider display, no automatic provider generation, no worker/queue/scheduler/polling, no CrewAI reintroduction, no model promotion, no raw rows/logs/notes/set rows exposure, no prompts/scratchpad/chain-of-thought storage, and no Streamlit theme cleanup.

Previous accepted milestones:
- Workout Plan Selection Persistence + Today Workout De-dup v1 (`d1077cc`)
- Daily Narrative Voice + Grounding / Copy Tuning v1 (`637a770`)
- Daily Narrative Coaching Intelligence + Voice Lab v1 (`a4ea288`)
- Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1 (`141a583`, merged to main at `644792d`)

Likely next step after this feature branch: Architecture review and QA acceptance for Daily Narrative Feedback-Driven Copy Rule Hardening v1.
