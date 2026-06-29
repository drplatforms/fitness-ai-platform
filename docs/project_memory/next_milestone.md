# Next Milestone — Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1

Owner: Backend Development with Architecture, QA, and Agent Engineering review.

Baseline: `feature/daily-coach-natural-draft-product-voice-audit-v2` at `9ba9579 Add daily coach natural draft product voice audit v2`.

Goal: fix the focused v2 QA failures without changing product architecture. The writer must stay loose; Product Voice Audit is a reviewer, not another pre-draft muzzle.

Required fixes:

- block final approval when fallback fails Product Voice Audit;
- represent no approved copy when final gates fail;
- make `reviewer_conclusion=fallback_failure` block final approval;
- calibrate Product Voice Audit so backend-shaped wording cannot receive product readiness 5;
- flag backend/app language such as `approved option`, `available options`, and `nutrition gap is open`;
- strengthen Food Action Language Contract for oatmeal/canned tuna user-facing actions;
- repair product-voice wording before fallback when factual claims are supported;
- preserve valid first-pass details during repair;
- add side-by-side status markers for accepted/rejected/fallback-blocked/no-approved-copy states.

Requested final status: `DAILY_COACH_PRODUCT_VOICE_AUDIT_CALIBRATION_FINAL_APPROVAL_GATE_FIX_V1_IMPLEMENTATION_COMPLETE`.
