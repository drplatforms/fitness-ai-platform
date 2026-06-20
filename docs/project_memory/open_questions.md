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

Resolved by Supercharger v1.1 - Session Brief Command:

- Dev Assistant can now generate a clean UTF-8 uploadable session brief with `python tools/dev_assistant.py session-brief --out qa_artifacts/session_brief.txt`.
- Session briefs replace fragile PowerShell transcript/Tee-Object/copy-paste handoff capture for normal ChatGPT session startup.
- Session brief output remains local-only under `qa_artifacts/` and is not source of truth.

Open after Supercharger v1.1:

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
- Should a future Supercharger v1.2 add a dedicated Architecture handoff packet command after session-brief stabilizes?

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

Resolved by runtime QA:

- `qwen3:8b` passed all required DailyCoachNarrativeContext users 101, 102, and 105 and remains the best practical evaluation candidate.
- `qwen2.5:3b` passed all required users as a safe compliance baseline but produced unacceptable meta/process copy.
- `qwen3:32b` remains a useful offline quality reference, but it timed out on user 101 and is too slow for practical preview loops.
- Daily Next Action-specific validation must now include product-copy filters for meta/process/internal architecture language.

Resolved by Provider Contract Tightening v1.1 implementation:

- The first meta/process rejection list is now implemented in the Daily Coach Narrative validator. It covers `approved facts`, `backend-approved`, `backend approved`, `exact approved focus`, `use the exact`, `use the approved`, `approved context`, `provided context`, `given context`, `as instructed`, `per instruction`, `according to the instructions`, `output contract`, `JSON`, `schema`, `validator`, `validation`, `backend facts`, `model output`, `provider output`, `deterministic facts`, `required focus`, `required facts`, `context packet`, `workflow target`, `deterministic fallback`, `backend`, `provider`, and `exact match`.

Open after v1.1 implementation:

- Does local runtime QA show that `qwen3:8b` remains approved for users 101, 102, and 105 after meta/process language tightening?
- Does `qwen2.5:3b` stop producing meta/process language, or is it now safely rejected as baseline-only copy?
- Should future Developer Preview use a debug endpoint, a local artifact viewer, or Streamlit Developer Mode only?
- Should `qwen3:14b` or `qwen3:30b-a3b` remain out of scope until after Developer Preview, given prior JSON reliability issues?
- What developer-only preview latency budget is acceptable for `qwen3:8b` if no normal Today UI integration is allowed yet?

Still not approved:

- normal Today UI integration
- Streamlit normal surface integration
- report integration
- model promotion
- qwen3 production approval
- direct_ollama default changes
- persistence of model-generated narrative output

## Daily Coach Narrative Provider Contract Tightening v1.1 Runtime Fix

Resolved by runtime-fix implementation:

- v1.1 validator failures are now field-specific for user-facing narrative copy.
- `avoided_claims` is treated as offline audit metadata, not product coach copy.
- provider prompt wording no longer uses `APPROVED_CONTEXT`, `APPROVED_FACTS`, or backend phrasing.
- provider-facing fact strings no longer expose workflow target route internals.
- context confidence language no longer tells the model to use backend-approved/internal phrasing.
- strict exact fact validation remains unchanged.

Open after runtime-fix implementation:

- Does `qwen3:8b` return to a clean practical pass on users 101, 102, and 105?
- Does `qwen2.5:3b` become safely rejected as baseline-only copy or produce acceptable coach copy without meta language?
- Is one more prompt-only pass needed before Developer Preview, or is v1.1 sufficient after runtime QA?
- Should Developer Preview hide `used_approved_facts` and `avoided_claims` entirely from normal UI surfaces?

## Daily Coach Narrative Developer Preview v1

Resolved by Developer Preview v1 implementation:

- The first developer-only preview surface is a backend debug endpoint: `GET /daily-coach/{user_id}/narrative-preview/debug`.
- The endpoint defaults to deterministic fallback and does not call a provider by default.
- The provider path is explicitly opt-in with `provider=direct_ollama`.
- Approved provider narrative appears only after parse and validation pass.
- Rejected/unparsable/provider-failed output falls back deterministically.
- Public-safe fallback reasons are used instead of raw validation errors or exception internals.
- Raw prompts, raw model output, raw provider payloads, stack traces, and validation internals are not returned.

Open after Developer Preview v1 implementation:

- Does local API runtime QA confirm provider-disabled fallback for users 101, 102, and 105?
- Does qwen3:8b pass or safely fall back through the debug endpoint for users 101, 102, and 105?
- Does qwen2.5:3b pass or safely fall back through the debug endpoint for users 101, 102, and 105?
- Should qwen3:32b be tested through the endpoint only as an optional offline/reference run due to latency?
- Should a Streamlit Developer Mode panel be added in a later v1.1 slice, or is backend debug endpoint coverage enough before Product Readiness Review?
- What latency budget is acceptable for a developer-only preview using qwen3:8b?

Still not approved:

- normal Today UI integration
- Streamlit normal surface integration
- report integration
- persistence of model-generated narrative
- model promotion
- qwen3 production approval
- direct_ollama default changes
- validator loosening
- deterministic fallback weakening


## Daily Coach Narrative Developer Preview v1 Closeout

Resolved by Developer Preview v1 acceptance:

- Local API runtime QA confirmed provider-disabled fallback for users 101, 102, and 105.
- qwen3:8b passed through the debug endpoint for users 101, 102, and 105 and remains a developer-preview evaluation candidate only.
- qwen2.5:3b is safe as a developer-preview baseline only.
- qwen3:32b remains optional offline/debug reference only due to latency.
- Backend debug endpoint coverage is enough before Product Readiness Review; Streamlit Developer Mode panel should be a later milestone.
- Developer-only preview latency around 40-50 seconds is acceptable for debug usage but not for normal Today UI.

Still not approved:

- normal Today UI integration
- Streamlit normal surface integration
- report integration
- persistence of model-generated narrative
- model promotion
- qwen3 production approval
- direct_ollama default changes
- validator loosening
- deterministic fallback weakening

## Daily Coach Narrative Async Today Preview Design v1

Resolved by design:

- Normal Today UI must not make synchronous provider calls.
- Today must show deterministic fallback immediately.
- First Today-adjacent implementation should be manual and developer-gated.
- Provider disabled remains the default.
- Approved provider output may display only after parse + validation success.
- Failed or rejected provider output keeps fallback.
- Rejected provider text, raw prompts, provider payloads, stack traces, and validation internals must remain hidden.
- No user-facing persistence/cache is approved for the first Today preview implementation.
- First recommended implementation after design acceptance is `Daily Coach Narrative Today Developer Panel v1`.

Open after design:

- Should the Developer Panel live under the existing Streamlit Developer Mode area or a dedicated Daily Coach debug expander?
- Should the panel call the accepted backend endpoint directly or use a small frontend helper wrapper?
- What exact label should be shown for fallback-vs-approved status in Developer Mode?
- Should the first panel include all public-safe metadata or only action, fallback, approved narrative, status, and latency?
- Should automatic background generation remain deferred until after Developer Panel QA?
- What provider disable switch should future normal UI use: environment config, query/debug gate, or a backend settings service?

Still not approved:

- automatic background generation from normal Today UI
- synchronous provider call from Today page load
- normal user-facing Coach Note card
- provider output persistence/cache
- model promotion
- direct_ollama default change

## Daily Coach Narrative Multi-Tier Async Today Preview Addendum

Resolved by Architecture addendum:

- The Today preview design must support multiple model lanes, not only `qwen3:8b`.
- `qwen3:8b` is the fast/practical developer-preview lane, not the final-quality target.
- `qwen3:32b` is the premium-quality developer-preview lane despite latency.
- `qwen2.5:3b` is the small baseline/regression lane.
- Deterministic fallback remains the immediate/default lane.

Open for the next implementation:

- Where should the model-lane selector live in Streamlit Developer Mode?
- Should lane labels be `Fallback`, `Fast`, `Premium`, and `Baseline`, or include model names directly?
- What timeout defaults should the Developer Panel use for fast vs premium lanes?
- Should premium lane execution be protected by an extra confirmation because it may take several minutes?
- Which public-safe status fields should be shown for each lane in the first panel implementation?

Still not approved:

- normal Today UI integration
- synchronous provider call from Today
- automatic background generation
- persistent narrative cache
- report integration
- model promotion
- qwen3 production approval
- direct_ollama default change

## Daily Coach Narrative Today Developer Panel v1

Open for QA:

- Does the panel remain hidden when Developer Mode is off?
- Does normal Today user view remain unchanged?
- Does deterministic fallback appear immediately in the Developer Mode panel?
- Does each provider lane require manual trigger only?
- Does the `qwen3:32b` premium lane warning communicate long runtime clearly enough?
- Do qwen3:8b, qwen3:32b, and qwen2.5:3b lanes either display approved output after validation or keep fallback safely?
- Are selected provider/model, fallback status, parse success, validation success, and latency shown clearly enough for QA?
- Is the curated context summary sufficient, or should future Developer Mode add more public-safe metadata?

Still not approved:

- normal Today UI narrative card
- automatic background generation
- persistence/cache
- report integration
- model promotion
- qwen3 production approval
- direct_ollama default change

## AI Coding Workflow Supercharger v1

Resolved by implementation:

- ChatGPT remains Architecture / TPM / QA review / handoff generator.
- User remains project owner, command runner, final approver, merge owner, and snapshot owner.
- Codex is optional and scoped, not the main implementation engine.
- Copilot is IDE helper only.
- Aider is optional for surgical patches/failing-test fixes.
- Dev Assistant is the local project cockpit for status, project-memory checks, prompt/context-pack generation, QA plans, snapshot commands, sync commands, and deterministic-safe restart guidance.
- Claude-specific files and commands remain out of scope.
- Headroom remains a future developer-workflow-only spike, not runtime product logic.

Open after Supercharger v1:

- Should Headroom Developer Workflow Spike v1 compress generated context packs, or remain a manual comparison only?
- Should Dev Assistant eventually gain a Linux runtime-QA helper script, or should it remain command-generation only?
- Should project-memory stale detection become stricter after more current_state/open_questions cleanup?
