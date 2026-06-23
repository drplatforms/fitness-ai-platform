
# Architecture Handoff Current

Milestone: Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: NEXT_ASYNC_JOB_CANDIDATE_SELECTION_V1_ACCEPTED

Summary:
- Fixed `lstop` SSH CRLF command handling in `scripts/fitness_commands.ps1` by LF-normalizing command script content and transporting it as UTF-8/base64 to remote Bash.
- Used `docs/project_memory/patterns/async_job_delivery_pattern_v1.md` to evaluate async candidates.
- Selected Weekly Coach Summary Async Job as the recommended next async job candidate.
- Recommended first milestone: Weekly Coach Summary Async Contracts + Data Model v1.
- No selected async job was implemented.
- No runtime product behavior changed.
- No provider behavior changed.
- No Streamlit behavior changed.
- No normal Today behavior changed.
- No worker/queue/scheduler/polling was added.
- No qwen3/qwen3:32b promotion occurred.
