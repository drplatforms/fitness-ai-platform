# Current State

Latest implemented milestone: Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1.

Daily Narrative now has a Developer Mode-only Voice Lab with synthetic safe scenario fixtures, deterministic candidates, style checks, and a safe local feedback capture loop. Users can mark generated copy as bad, better, or approved; save rejected phrases; save preferred rewrites; and preserve scenario/candidate/reason-code context for future deterministic/provider copy tuning.

Previous accepted milestone: Daily Narrative Coaching Intelligence + Voice Lab v1 (`a4ea288`). That milestone created the lab and made concrete copy critique possible. This milestone turns that critique into app-side copy memory.

Feedback persistence is local and safe by default. Runtime feedback records must not include raw food logs, raw workout rows, raw check-in notes, raw set rows, prompts, scratchpad, chain-of-thought, or secrets.

Boundaries remain: no model promotion, no public/default provider display, no automatic generation, no worker/queue/scheduler/polling, no CrewAI reintroduction, no raw rows/logs/notes/set rows exposure, and no Streamlit theme cleanup.
