# Open Questions — Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

1. Does completion diagnostics prevent/identify cut-off free-range drafts clearly enough for QA to trust first-pass artifacts?
2. Do display-ready numeric fields prevent raw `.0`, alarming deficit ranges, enum capitalization, and awkward macro prose from leaking into coach copy?
3. Do macro and food option cards make dense nutrition data easier to inspect without replacing the full coach note?
4. Do AI snack candidates give the model practical food combinations without inventing foods outside the candidate pool?
5. Does bounded practical food seeding improve carb/fat/calorie guidance when more than lean protein is needed?
6. Does weight-trend anomaly handling suppress low-confidence 22 lb-style signals from coach copy while preserving raw debug evidence?
7. Does session naming visibility make clear whether the model saw an internal workout model label or a user-facing session name?
8. Do voice-style findings preserve useful coach energy without allowing unsafe hypeman advice?
9. Does the live GPT-5.5 run show stronger, more complete, better formatted first-pass notes after v3?

Closed boundaries for this milestone:

- developer-only tooling
- full note preserved; no Today-card renderer/compressor
- normal Today unchanged
- deterministic remains default
- OpenAI/direct_ollama explicit opt-in/evaluation-only
- no provider promotion
- no production persistence of provider output
- no raw provider envelopes, secrets, or raw DB rows in artifacts
- no public UI
- no restrictive reviewer/renderer gate or phrase-ban loop
- no meal planning/workout generation/nutrition target/recovery score changes
- no RAG, embeddings, multi-agent runtime, local/cheaper model comparison, Headroom/context compression, or full food expansion

Known baseline drift remains documented and unpatched: `tests/test_daily_narrative_rich_day_service.py` expected `Read the day before adding more` vs actual `Consider the full day`.

---

# Open Questions — Daily Coach Free-Range Voice + Precision + Payload Enrichment v2

1. Which voice variant produces the strongest full coach note: practical, direct, strict, empathetic, or hypeman?
2. Does precision metadata reduce unnecessary `about`/`roughly` wording when values are direct while preserving hedging for estimates?
3. Does expanded food candidate structure improve useful food guidance without inventing foods, servings, timing, pairings, or claims?
4. Does `model_input_manifest.md` make it clear exactly what the model saw before Architecture judges copy quality?
5. Is set-level workout data available in this path, and if not, is the absence/reason documented clearly enough for future Workout Set Intelligence work?
6. Do recovery fields remain broad enough to support the strongest part of the free-range note?
7. Are post-hoc diagnostics useful without becoming generation-time phrase bans or product approval gates?
8. Does repeated live GPT-5.5 output become more consistent after voice and precision enrichment?

Closed boundaries for this milestone:

- developer-only tooling
- full note preserved; no Today-card renderer/compressor
- normal Today unchanged
- deterministic remains default
- OpenAI/direct_ollama explicit opt-in/evaluation-only
- no provider promotion
- no production persistence of provider output
- no raw provider envelopes or secrets in artifacts
- no raw DB rows
- no public UI
- no phrase-ban or Product Voice Audit rewrite
- no meal planning/workout generation/nutrition target/recovery score changes
- no RAG, embeddings, multi-agent runtime, local model comparison, or full food expansion

Known baseline drift remains documented and unpatched: `tests/test_daily_narrative_rich_day_service.py` expected `Read the day before adding more` vs actual `Consider the full day`.

---

# Open Questions — Daily Coach Full User-Day Free-Range Payload Baseline v1

1. Does GPT-5.5 produce more natural, useful Daily Coach copy when the provider prompt contains neutral user-day data instead of app-generated coach prose?
2. Does the exact `provider_input_prompt.md` confirm no app-copy cage, old Daily Coach example, deterministic fallback copy, Product Voice Audit finding, or phrase-ban wall is being fed to the model?
3. Does the full user-day packet include enough nutrition, training, recovery, and uncertainty context for useful synthesis?
4. Does the broader food candidate list improve food guidance without causing invented servings, timing, pairings, or unlogged-food claims?
5. Do repeated runs show usable consistency, or is quality a one-off lucky draft?
6. Do post-hoc app-copy and claim-risk diagnostics catch unsupported facts without altering first-pass output?
7. Is token/cost acceptable for a future provider lane if Architecture later chooses to promote any version of this path?
8. If free-range first-pass output is still backend-shaped, should Architecture route to deterministic phrase-source cleanup, a different payload design, or abandon provider copy for Daily Coach?

Closed boundaries for this milestone:

- developer-only tooling
- normal Today unchanged
- deterministic remains default
- OpenAI/direct_ollama explicit opt-in/evaluation-only
- no provider promotion
- no production persistence of provider output
- no raw provider envelopes or secrets in artifacts
- no raw DB rows
- no public UI
- no Product Voice Audit rewrite
- no phrase-ban milestone
- no meal planning/workout generation/nutrition target/recovery score changes
- no RAG, embeddings, or multi-agent runtime

Known baseline drift remains documented and unpatched: `tests/test_daily_narrative_rich_day_service.py` expected `Read the day before adding more` vs actual `Consider the full day`.

---

# Open Questions — Daily Coach Wide Context Copy Cleanup + QA Readability v1

## Active

1. Does prompt/context cleanup reduce backend-shaped wording in first-pass wide-context copy without rebuilding the old phrase cage?
2. Does the writer-facing context now encourage plain food language such as `if protein is still short` instead of internal language such as `approved option` or `gap is still open`?
3. Do terminal-friendly artifacts make QA review faster and less error-prone?
4. Does the product-language scan surface copy problems without becoming a new approval gate?
5. Does `wide_context_practical_coach` remain the best current variant after cleanup?
6. Should the next architecture step be another live GPT-5.5 QA run, or a design pass for promoting only the strongest first-pass architecture ideas into the Daily Coach provider path?

## Known baseline drift

- `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied `718c614` / `42d0bd4` lineage.
- Example mismatch: expected `Read the day before adding more`; actual `Consider the full day`.
- Architecture decision: document this drift and do not patch it inside unrelated wide-context copy/readability work.
- Full-suite green must not be claimed if the drift remains.

## Closed/unchanged boundaries

- Wide-context copy cleanup remains developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, approved context, artifact safety, and future approval decisions.
- Raw provider envelopes are not persisted in default artifacts.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, queue, or production provider promotion is included.
