
# Backend Handoff Current

Milestone: Next Async Job Candidate Selection v1 + lstop Tooling Hotfix

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Backend notes:
- `lstop` now uses the shared LF-normalized SSH command transport through `Invoke-FitnessLinux`.
- Because the shared transport helper was touched, validate `lstop` and `app` from Windows PowerShell before final acceptance.
- Candidate selection only selected Weekly Coach Summary Async Job; it did not implement the job.
- Next Backend implementation should wait for Architecture to authorize Weekly Coach Summary Async Contracts + Data Model v1.
- Do not jump directly to provider runtime.
- Do not add worker/queue/scheduler/polling without design authorization.
