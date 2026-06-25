# Daily Narrative Voice + Grounding / Copy Tuning v1

Status: Implemented / ready for review.

Goal: tune Daily Narrative deterministic and provider-facing copy so grounded output no longer defaults to mechanical “useful move” / “clearer picture” language.

Scope:

- Add Daily Narrative copy service and voice contract.
- Move selected-date QA next-action copy into reason-code/fact-driven copy families.
- Make limited-data copy cautious even when several domains are present.
- Keep rich-data copy focused on interpretation rather than generic meal/snack logging.
- Add provider-facing banned phrase and good/bad example guidance.
- Add validator checks for mechanical Daily Narrative phrases.
- Preserve factual validation, deterministic fallback, Developer Mode QA preview, and normal Today boundaries.

Non-goals preserved:

- No model promotion.
- No qwen3:8b, 14B, or 32B promotion/call.
- No public/default provider display.
- No automatic generation, worker, queue, scheduler, or polling.
- No CrewAI reintroduction.
- No raw rows/logs/notes/set rows exposure.
- No workout selection changes beyond regression preservation.
