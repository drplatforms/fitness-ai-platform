# Open Questions

Last updated: 2026-06-18

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


## Coach Voice Bakeoff

Bounded Coach Voice Bakeoff v1 is accepted with model findings. The direct CLI entrypoint is patched so repo-root execution no longer requires manual `PYTHONPATH`.

Resolved by bakeoff v1:

- qwen3:8b passed all 3 required starter contexts and is the best practical bounded coach voice candidate so far.
- qwen3:32b passed all 3 starter contexts as an exploratory addendum and is the best offline / chores-mode quality signal so far.
- qwen3:32b latency is too high for tight Today UI, roughly 2.6-3.1 minutes per context.
- qwen2.5:3b and qwen3:14b failed the current output contract.
- No model is promoted by the bakeoff.
- The next milestone should be Coach Voice Contract Tightening v1.

Open after bakeoff v1:

- Which prompt/schema packaging changes prevent schema echoing and improve object-format reliability?
- Can qwen2.5:3b and qwen3:14b pass after contract tightening, or are their failures model-specific?
- Does qwen3:8b remain safe across all five context packs after contract tightening?
- Should qwen3:32b remain a reference-only offline quality signal or be tested for slower report/reflection modes later?
- What validator gaps appear when all five context packs are evaluated?
- What evidence threshold would be required before planning a future Daily Coach Narrative v1?

No model is promoted by the bakeoff itself.

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

## Coach Voice Contract Tightening v1 QA questions

Status: PENDING RUNTIME QA

Questions for the all-context bakeoff run:

- Does the tightened contract reduce schema echoing for `qwen2.5:3b`, `qwen3:14b`, or `qwen3:30b-a3b`?
- Does `qwen3:8b` remain the best practical evaluation-only candidate across all five contexts?
- Does `qwen3:32b` remain the best offline / chores-mode quality reference across all five contexts?
- Does `qwen3:14b` improve enough to justify Practical Model Comparison v2?
- Does `qwen3:30b-a3b` remain incompatible with the strict JSON-only contract, or does the tightened prompt help?
- Are failure categories clearer enough to guide a possible Coach Voice Contract Tightening v2?
- Is the next safe milestone Daily Coach Narrative v1 Planning, Practical Model Comparison v2, Offline Report Voice Mode v1 Planning, or another contract-tightening slice?

Non-negotiable constraints:

- no model promotion
- no qwen3 production approval
- no Today integration
- no report integration
- no validator loosening
- no provider path changes
- no direct_ollama default change
