# Next Milestone — Daily Coach Natural Draft + Product Voice Audit v2

Owner: Backend Development with Agent Engineering advisory and QA validation.

Baseline: `main` at `4104796 Merge daily coach natural draft claim audit v1`.

Goal: extend Natural Draft + Claim Audit with a separate Product Voice Audit and first-pass visibility so QA can see whether GPT-5.5 wrote useful coaching, whether audit/repair/fallback damaged it, and whether final approved copy is actually better than deterministic fallback.

Required outputs:

- preserve first-pass model draft before claim audit, product voice audit, repair, or fallback;
- add `first_pass_model_draft_before_audit.md`;
- add side-by-side comparison of deterministic fallback, first-pass draft, repaired draft, and final approved copy;
- add Product Voice Audit service and summary artifact;
- add Food Action Language Contract service for eating-language food actions;
- humanize fallback and require fallback to pass Product Voice Audit;
- record repair deltas;
- record reviewer conclusions identifying model/brief/audit/repair/fallback/product voice bottlenecks;
- keep normal Today behavior unchanged and provider use developer-only;
- add focused tests and project memory docs.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_IMPLEMENTATION_COMPLETE`.
