# Project Continuity Bootstrap

Current focus: AI Health Coach / fitness_ai.

Latest implemented feature branch milestone: Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1.

Key rule: backend tells the truth; provider improves voice; validator decides what survives; deterministic fallback always works.

Daily Narrative now has a Developer Mode-only Voice Lab with synthetic scenario fixtures and local feedback capture. Users can mark generated copy as bad, better, or approved; save rejected phrases; save preferred rewrites; and preserve scenario/candidate/reason-code context for future copy hardening. Feedback capture is app-side memory, not model memory.

Current feedback storage: local JSONL via `artifacts/daily_narrative_feedback.jsonl` by default, or `DAILY_NARRATIVE_FEEDBACK_PATH` when configured. Runtime feedback files are not intended to be committed.

Boundaries: no public/default Daily Narrative provider display, no automatic provider generation, no worker/queue/scheduler/polling, no CrewAI reintroduction, no model promotion, no raw rows/logs/notes/set rows exposure, no prompts/scratchpad/chain-of-thought storage, and no Streamlit theme cleanup.

Previous accepted milestones:
- Workout Plan Selection Persistence + Today Workout De-dup v1 (`d1077cc`)
- Daily Narrative Voice + Grounding / Copy Tuning v1 (`637a770`)
- Daily Narrative Coaching Intelligence + Voice Lab v1 (`a4ea288`)

Likely next milestone after acceptance: Daily Narrative Feedback-Driven Copy Rule Hardening v1.
