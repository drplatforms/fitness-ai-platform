# Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1

Status: Implemented / ready for architecture review.

This milestone adds Developer Mode feedback capture to the Daily Narrative Voice Lab.

The user can mark deterministic Voice Lab copy as `bad`, `better`, or `approved`, capture rejected phrases, add preferred rewrites, and save notes with scenario/candidate/reason-code context.

## Implemented

- Added safe local Daily Narrative feedback persistence.
- Added feedback record model and save/list/export helpers.
- Added Developer Mode feedback controls under Voice Lab candidates.
- Added CLI feedback list/export/summary support.
- Preserved scenario ID, scenario label, candidate text, reason codes, data quality, confidence, domains present/missing, coaching angle, copy-quality warnings, and optional preferred rewrite.
- Set `raw_data_included` to `false` for all records.
- Rejected private/debug content such as raw logs, secrets, prompts, scratchpad, and chain-of-thought markers.
- Updated app-side voice examples with known user feedback, including “adding random data” and “before you treat the plan as automatic.”

## Boundaries

- Developer Mode only.
- No normal Today behavior changes.
- No provider call on save or page load.
- No automatic copy rewriting.
- No model memory assumption.
- No model promotion.
- No CrewAI.
- No worker, queue, scheduler, polling, or background process.
- No raw rows/logs/notes/set rows persisted in feedback.
- No prompts, scratchpad, chain-of-thought, or secrets stored.
