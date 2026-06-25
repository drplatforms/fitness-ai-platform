# Current State

Latest implemented milestone: Daily Narrative Voice + Grounding / Copy Tuning v1.

Daily Narrative now has a project-owned voice contract and copy service. Selected-date QA copy is driven by facts/reason families instead of generic default phrases. The app avoids mechanical “useful move” / “clearer picture” style language in deterministic QA preview copy, keeps limited-data copy cautious, and keeps rich-data copy focused on interpretation instead of generic meal/snack logging.

Provider-facing Daily Narrative prompt guidance now includes banned phrases plus good/bad examples. Provider candidates are still parsed and validated before approval, and mechanical copy is rejected by the validator.

Previous accepted milestone: Workout Plan Selection Persistence + Today Workout De-dup v1 (`d1077cc`). Workout page remains canonical for Plan / Active / Review. Today remains compact and does not duplicate the full workout selection workflow.

Boundaries remain: no model promotion, no public/default provider display, no automatic generation, no worker/queue/scheduler/polling, no CrewAI reintroduction, no raw rows/logs/notes/set rows exposure, and no Streamlit theme cleanup.
