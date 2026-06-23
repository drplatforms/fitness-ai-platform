
# Open Questions

## Next Async Job Candidate Selection v1

Current status:
Next Async Job Candidate Selection v1 + lstop Tooling Hotfix is implemented and ready for Architecture review.

Selected next async job candidate:
Weekly Coach Summary Async Job

Recommended first milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Open after acceptance:

- Architecture should approve or revise the Weekly Coach Summary recommendation.
- Architecture should decide whether the first milestone is contracts/data model only or service shell/no worker.
- QA should review the candidate matrix and the no-provider/no-normal-Today boundaries.

## Tooling backlog

Completed in this milestone:
`lstop` SSH CRLF command handling was fixed by LF-normalizing Linux command text and transporting it safely to remote Bash.

Still watch:
- Confirm `app` behavior remains preserved when validating the shared SSH helper path.
- Confirm `lrestart` behavior remains preserved if directly tested.

## Portfolio / LinkedIn / GitHub

Portfolio / LinkedIn / GitHub update remains deferred until a stable end-to-end persisted async workflow is ready to describe cleanly.
