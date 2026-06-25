# QA Handoff Current

Milestone: Daily Narrative User Feedback Capture + Preferred Rewrite Loop v1

QA focus:
- feedback labels: bad / better / approved
- rejected phrase capture
- preferred rewrite capture
- feedback persists after rerun
- list/export works
- feedback excludes raw/private/debug data
- saving feedback does not call provider
- normal Today remains unchanged with Developer Mode off
- workout selection regression still passes

Manual smoke examples:
- recovery_present_training_planned: reject "before you treat the plan as automatic" and save preferred rewrite.
- rich_day_multiple_domains: reject "adding random data" and save preferred rewrite.
