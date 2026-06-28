# Daily Coach Natural Draft + Product Voice Audit v2

Status: Backend implementation in progress.

Baseline: `main` at `4104796 Merge daily coach natural draft claim audit v1`.

Requested status: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_IMPLEMENTATION_COMPLETE`.

## Intent

V2 extends Natural Draft + Claim Audit with product-quality review and artifact visibility. The writer should be allowed to draft naturally from a rich approved brief; backend review decides whether the result is factual and useful enough.

Core mandate:

- loosen the writer;
- tighten the reviewer;
- expose the first draft;
- compare honestly;
- treat deterministic fallback as the floor, not the goal.

## Implemented direction

- first-pass draft capture before audit/repair/fallback;
- Product Voice Audit separated from factual Claim Audit;
- Food Action Language Contract for eating-language food actions;
- humanized deterministic fallback;
- side-by-side output comparison;
- repair delta summary;
- humanized fallback summary;
- reviewer conclusion artifact;
- final approval requires factual audit plus product voice audit;
- developer-only CLI/artifact flow remains non-product.

## Boundaries

Normal Today behavior is unchanged. OpenAI/direct_ollama remain opt-in/evaluation-only. No provider promotion, parser relaxation, final approval bypass, raw DB exposure, raw provider persistence, public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery score changes, worker, scheduler, or queue changes are included.

---

## Focused Patch — Product Voice Audit Calibration + Final Approval Gate Fix v1

Status: routed back to Backend after QA failure.

QA result for v2: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_QA_FAIL_APPROVAL_LOGIC_AND_AUDIT_CALIBRATION`.

Patch status requested: `DAILY_COACH_PRODUCT_VOICE_AUDIT_CALIBRATION_FINAL_APPROVAL_GATE_FIX_V1_IMPLEMENTATION_COMPLETE`.

Fix scope:

- final approval now requires all final gates to pass;
- fallback Product Voice Audit failure blocks final approved copy;
- failed final gates produce `no_approved_copy` rather than silently using bad fallback;
- reviewer conclusions are enforcement signals, not passive metadata;
- Product Voice Audit calibration now treats product readiness 5 as shippable with no edit;
- backend/app food language and gap-language are product findings;
- Food Action Language Contract blocks mechanical food actions such as `have dry oats`, `add dry oats`, `use canned tuna`;
- repair is preferred over fallback for factually safe, repairable product wording issues;
- side-by-side comparison marks candidate statuses including `fallback_blocked` and `no_approved_copy`.

The patch must not add another writer cage. It improves the reviewer/editor after generation.
