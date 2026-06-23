# QA Handoff Current

Milestone: Async Job Delivery Pattern / Playbook v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

QA focus:
- Review `docs/project_memory/patterns/async_job_delivery_pattern_v1.md` as the reusable QA baseline for future async jobs.
- Confirm the playbook includes disabled/default smoke, Developer Mode inspection smoke, provider disabled path smoke, provider enabled path smoke when relevant, failure/fallback smoke, preview bridge boundary smoke, normal UI metadata leak checks, Developer Mode diagnostic boundary checks, regression tests, project memory checks, and fsweep clean.
- This milestone does not require app smoke because no runtime files changed.
- lstop/lrestart/app CRLF issue is backlog only and not fixed here.
