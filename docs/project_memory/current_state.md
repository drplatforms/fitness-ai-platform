
# Current State

Latest accepted milestone:
Async Job Delivery Pattern / Playbook v1

Current milestone:
Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Current status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
NEXT_ASYNC_JOB_CANDIDATE_SELECTION_V1_ACCEPTED

Current behavior:

- `lstop` SSH command transport now LF-normalizes Linux command script content before remote Bash execution.
- `lstop`, `app`, and `lrestart` remain Windows PowerShell helper commands that SSH into Linux.
- No runtime product behavior changed.
- No provider behavior changed.
- No Streamlit behavior changed.
- No normal Today behavior changed.
- No selected async job was implemented.
- Weekly Coach Summary Async Job is selected as the recommended next async job candidate.
- Recommended first implementation milestone is Weekly Coach Summary Async Contracts + Data Model v1.

Important docs:

- `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`
- `docs/project_memory/reviews/next_async_job_candidate_selection_v1.md`
- `docs/project_memory/milestones/next_async_job_candidate_selection_v1.md`

Still not authorized:

- Weekly Coach Summary implementation
- provider execution from Today
- provider execution on page load
- automatic async job generation
- public/default async narrative display
- worker / queue / scheduler / polling
- qwen3 bridge or promotion
- qwen3:32b promotion
