
# Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
NEXT_ASYNC_JOB_CANDIDATE_SELECTION_V1_ACCEPTED

## Scope

This milestone completes two bounded tasks:

1. Fix the known `lstop` CRLF SSH command handling issue in `scripts/fitness_commands.ps1`.
2. Use the accepted Async Job Delivery Pattern / Playbook to select and scope the next async job candidate.

## Selected next async candidate

Weekly Coach Summary Async Job

## Recommended first implementation milestone

Weekly Coach Summary Async Contracts + Data Model v1

## Why this candidate

Weekly Coach Summary is the best next async candidate because it is naturally async, high-value, deterministic-first, lower risk to normal Today behavior, and strong for portfolio/demo storytelling.

## Non-goals

- no selected async job implementation
- no provider runtime changes
- no worker / queue / scheduler / polling
- no normal Today behavior change
- no Streamlit behavior change
- no Daily Coach async runtime behavior change
- no approved preview bridge behavior change
- no qwen3/qwen3:32b promotion
- no broad command helper rewrite

## Validation expectations

- project memory checks pass
- docs/current handoffs updated
- `lstop` passes from Windows PowerShell
- `app` behavior preserved if shared helper path is validated
- `lrestart` behavior preserved if shared helper path is validated
- fsweep clean
