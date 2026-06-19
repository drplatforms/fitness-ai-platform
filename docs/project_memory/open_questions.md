# Open Questions

Last updated: 2026-06-19

## Daily Coaching Product Loop

Resolved for v1:

- Daily Next Action Panel v1 uses a deterministic backend service and stable API route before Streamlit renders it.
- Priority order is recovery/safety, missing recovery input, nutrition logging completeness, workout readiness, report guidance, then data-quality/nutrition-target progress.
- Workflow targets are limited to existing surfaces: Today recovery check-in, Today workout, Nutrition quick log, Nutrition target-vs-actual, Workout preview, and Reports guidance.
- Seeded QA classes are defined for users 101, 102, and 105.

Open after v1 implementation:

- Should future versions support a secondary action, or should Today remain strictly one primary action?
- Should workflow targets become real Streamlit navigation anchors after UI navigation is formalized?
- Should action availability be persisted for analytics, or remain read-only/computed at request time?
- How should the panel behave once catalog expansion and food logging usability improve?


## Catalog Expansion & Curation

Catalog Expansion & Curation v1 planning accepted Food Catalog Expansion v1 as the first implementation slice and Exercise Catalog Expansion v1 as the next product-usability slice.

Resolved through Food Catalog Expansion v1 implementation:

- Food Catalog Expansion v1 starts with curated seed entries rather than a schema migration.
- The starter canonical food catalog is expanded from 132 to 202 entries.
- New entries keep current per-100g nutrient storage, default grams, source policy, confidence, and alias infrastructure.
- The implementation stays deterministic, manually curated, reviewable, and backend-owned.
- Fiber and sodium remain optional/future nutrients rather than required v1 fields.
- Brand-heavy, highly variable mixed foods, scraping, RAG, embeddings, AI-generated production entries, and meal planning remain out of scope.

Resolved through Exercise Catalog Expansion v1 implementation:

- Exercise Catalog Expansion v1 starts with curated seed entries and existing schema fields rather than a schema migration.
- The curated local exercise catalog expands from 178 to 240 entries.
- New entries improve home-gym coverage across dumbbell, barbell/rack/plates, EZ bar, cable, bands, pull-up bar, treadmill, bike, bodyweight, and mobility/recovery options.
- Movement-pattern coverage expands while keeping current deterministic filtering and workout preview behavior.
- Recovery suitability, joint stress, substitution group, progression type, setup notes, and safety notes remain future schema/design work rather than forced into v1.
- Scraping, RAG, embeddings, AI-generated production entries, provider changes, workout generation rewrites, and Streamlit redesign remain out of scope.

Open after catalog v1 slices:

- Should a future food schema migration add first-class category fields beyond `food_type`?
- Should future quick-log UX use default serving sizes as shortcuts, or continue requiring explicit grams?
- Should Food Catalog Expansion v2 add fiber and sodium for a smaller high-confidence subset?
- Which new foods should be prioritized from actual user logging misses after QA?
- Should Exercise Catalog Expansion v2 add first-class joint stress, recovery suitability, substitution group, setup notes, and safety notes?
- Should workout generation begin using explicit recovery-suitability tags after a schema review?
- What acceptance threshold should be used before considering the food and exercise catalogs broad enough for demo/recruiter walkthroughs?


## Coach Voice Bakeoff / Contract Tightening

Resolved by Bounded Coach Voice Bakeoff v1 and Coach Voice Contract Tightening v1:

- qwen3:8b remains the best practical evaluation-only bounded coach voice candidate.
- qwen3:32b remains the best offline / chores-mode quality reference.
- qwen2.5:3b improved from output-contract failure to 5/5 pass across all five context packs, but remains more generic.
- qwen3:14b partially improved to 2/5 but remains unreliable.
- qwen3:30b-a3b remains incompatible with strict JSON-only output.
- Prompt/schema packaging was a real contributor to prior failures.
- No model is promoted.
- Daily Coach Narrative v1 Planning is the next safe bridge milestone.

Open after contract tightening:

- How much additional validation is needed before a future narrative provider can be tested behind an opt-in flag?
- Should qwen2.5:3b be retained as a small compliant baseline despite generic language?
- Should qwen3:32b remain offline/reference-only due to latency?
- Should future narrative QA reuse the all-five-context bakeoff set or define Daily Next Action-specific fixtures?

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- After accepted forced-fallback runtime QA, should public claims be updated to say Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode?
- Should a future production-like fallback QA scenario be designed, or is the QA-only forced-invalid mode sufficient for portfolio claims and regression protection?
- Should Nutrition remain opt-in indefinitely after Level 5 runtime validation, or should a separate future default-provider readiness review be planned?
- What additional non-seeded runtime cases are required after Level 5 promotion, if any?
- What additional negative validator cases are required after observing real qwen2.5 approved output in matrix runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?
- Should debug/QA-only Nutrition validation diagnostic categories remain limited to `/reports/status/{job_id}/debug`, or should Architecture define a broader debug-only QA surface later?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?

## Daily Coach Narrative v1 Planning / Context Builder

Resolved by planning:

- The narrative may explain the deterministic Daily Next Action but may not choose or change it.
- Backend owns action selection, workflow target, approved focus, confidence limits, approved facts, forbidden claims, validation, and fallback.
- The model owns wording, tone, concise explanation, and coach-like framing only.
- The proposed output contract reuses the tightened coach voice JSON object.
- Failed provider output falls back to deterministic Daily Next Action wording.

Resolved by Context Builder v1 implementation:

- The context builder lives in `services/daily_coach_narrative_context_service.py`.
- The model lives in `models/daily_coach_narrative_models.py`.
- Required context fields now include user/date/action id/title/reason/workflow target/priority/severity/approved focus/confidence language/approved facts/approved limitations/forbidden claims/fallback note/source metadata/status.
- `approved_focus` is exactly the Daily Next Action title.
- `approved_facts` are generated directly by the context builder from Daily Next Action public fields and public-safe evidence.
- Raw logs, raw provider output, debug payloads, full catalog dumps, validation internals, and unfiltered history remain excluded.
- No model call is introduced.

Open after Context Builder v1:

- What compact length limit should the future Today card use for `coach_note`?
- Should Daily Coach Narrative Offline Provider Runtime QA use fixed fixtures, live seeded users 101-105, or both?
- Should `qwen2.5:3b` be tested as a fallback candidate despite more generic copy?
- Should `qwen3:32b` remain offline/reference-only for narrative QA, or be skipped due to latency?
- What Developer Mode preview surface is acceptable before normal Today UI integration?
- What additional validator phrases are needed for Daily Next Action-specific risk areas?
- Should an optional debug-only context endpoint be added before provider runtime QA, or should context stay service/test-only for now?

Non-negotiable constraints:

- no model promotion
- no qwen3 production approval
- no Today integration during planning/context-builder work
- no report integration
- no validator loosening
- no provider path changes
- no direct_ollama default change
- no raw model/debug/provider leakage in normal UI

## Daily Coach Narrative Offline Provider QA v1

Open during runtime QA:

- Does `qwen3:8b` pass all required DailyCoachNarrativeContext users 101, 102, and 105?
- Does `qwen2.5:3b` remain contract-compliant but generic, or does the real context improve usefulness?
- Does `qwen3:32b` provide a meaningful offline quality signal relative to its runtime cost?
- Are any Daily Next Action-specific forbidden claim fragments missing from the validator?
- Should future Developer Preview use a debug endpoint, a local artifact viewer, or Streamlit Developer Mode only?
- Should `qwen3:14b` or `qwen3:30b-a3b` be retried later, or are they out of scope until a contract-tightening v1.1?

Still not approved:

- normal Today UI integration
- Streamlit normal surface integration
- report integration
- model promotion
- qwen3 production approval
- direct_ollama default changes
- persistence of model-generated narrative output
