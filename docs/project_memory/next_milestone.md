
# Next Milestone

Current authorized milestone:
Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
NEXT_ASYNC_JOB_CANDIDATE_SELECTION_V1_ACCEPTED

Purpose:
Fix the known `lstop` SSH CRLF issue and use the accepted Async Job Delivery Pattern / Playbook to select the next async job candidate before implementation begins.

Selected next async job candidate:
Weekly Coach Summary Async Job

Recommended first implementation milestone after acceptance:
Weekly Coach Summary Async Contracts + Data Model v1

Why:
Weekly Coach Summary is naturally async, deterministic-first, high product value, lower risk to normal Today behavior, and strong portfolio/demo value.

Still not authorized:

- Weekly Coach Summary implementation
- provider runtime changes
- normal Today provider execution
- provider execution on page load
- automatic async job generation
- worker / queue / scheduler / polling
- public/default async narrative display
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
