# Review: Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1

Status: Ready for architecture review.

## Summary

Developer Mode Daily Narrative Voice Lab now has a safe feedback loop. The user can mark generated copy as bad, better, or approved; save a rejected phrase; save a preferred rewrite; and preserve the scenario/candidate context needed for future copy tuning.

## Acceptance Notes

- Feedback capture is app-side copy memory, not model memory.
- Feedback is stored locally as JSONL by default under `artifacts/daily_narrative_feedback.jsonl` or in a path configured by `DAILY_NARRATIVE_FEEDBACK_PATH`.
- Runtime feedback files are not meant to be committed.
- The implementation supports list/export helpers for Developer Mode QA.

## Follow-up

The next useful milestone is Daily Narrative Feedback-Driven Copy Rule Hardening v1, where captured examples should update deterministic copy families, provider prompt examples, and banned/awkward phrase lists.
