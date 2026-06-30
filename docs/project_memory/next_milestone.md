# Next Milestone — Daily Coach Fully Free Source-Data Lab v1

Recommended branch:

```text
feature/daily-coach-fully-free-source-data-lab-v1
```

Baseline:

```text
main @ 56d63c4
fitness_ai_snapshot_2026-06-29_56d63c4_main_merge-daily-coach-free-range-decaging-diagnostic-baseline-v4.zip
```

Implementation focus:

- Add separate developer-only fully free source-data lab tool.
- Build clean source-data packet artifacts instead of coach packets or backend conclusions.
- Use a short minimal prompt with safety boundaries only.
- Capture exact first-pass drafts before diagnostics.
- Add source-data completeness, model freedom, backend-prose contamination, completion, claim-risk, token/cost, and artifact-safety artifacts.
- Keep OpenAI/GPT-5.5 opt-in only and normal Today unchanged.

Do not implement RAG, embeddings, vector search, multi-agent orchestration, production Today replacement, provider promotion, or full food catalog expansion in this milestone.

---

# Next Milestone — Daily Coach Free-Range Prompt + Payload Decaging v4

Source baseline: `feature/daily-coach-free-range-output-completion-coach-surface-polish-data-seeding-v3` at `c36c50a Polish free range output and data seeding`.

Backend branch: `feature/daily-coach-free-range-prompt-payload-decaging-v4`.

Requested status: `DAILY_COACH_FREE_RANGE_PROMPT_PAYLOAD_DECAGING_V4_IMPLEMENTATION_COMPLETE`.

Architecture decision: continue the free-range Daily Coach experiment. Do not merge v3 yet, do not move to docs cleanup, do not onboard new Architecture continuation, do not route to a restrictive renderer/reviewer gate, and do not solve remaining copy issues with a phrase-ban loop.

Required implementation:

- keep deterministic provider runnable without `--allow-live-provider` while preserving live-provider opt-in for OpenAI/direct_ollama;
- split internal/debug payload details from the model-facing coach-facts surface;
- add `model_facing_coach_facts.md` and `model_facing_coach_facts.json`;
- add `decaging_summary.md`;
- add `backend_label_exposure_summary.md`;
- add `--prefer-decaged-prompt` so provider input can use clean coach facts instead of the backend-shaped packet;
- tell the model not to echo field labels/internal categories or turn backend wording into prose;
- give GPT-5.5 editorial permission to choose what matters instead of mentioning every number;
- keep dense numeric details in compact cards when useful rather than the main coach paragraph;
- reduce repeated `roughly` wording by introducing approximate meal options once;
- prevent `roughly 0g fat`-style deterministic card artifacts;
- keep completion diagnostics and include expected/captured/complete/truncated/skipped counts;
- preserve exact first-pass drafts before diagnostics, repair, fallback, or phrase cleanup;
- add direct/hypeman clean variants and keep hypeman energy bounded;
- update pasteback report with model-facing facts, decaging, backend label exposure, completion counts, food/snack formatting, macro range framing, Markdown leak review, claim risk, consistency, token/cost, artifact safety, and known baseline drift.

Boundaries:

- developer-only experiment;
- normal Today unchanged;
- no production Today replacement;
- no restrictive reviewer/renderer gate;
- no OpenAI default or provider promotion;
- no public UI or Streamlit controls;
- no raw provider envelope persistence, secrets, or raw DB dumps;
- no medical advice generation;
- no meal planning/workout generation/nutrition target/recovery score changes;
- no RAG, embeddings, multi-agent runtime, local/cheaper model comparison, Headroom/context compression, project-memory handoff compression, stale-doc hygiene, or full 450–500 food expansion.

Known baseline drift remains documented and unpatched: `tests/test_daily_narrative_rich_day_service.py` expected `Read the day before adding more` vs actual `Consider the full day`.
