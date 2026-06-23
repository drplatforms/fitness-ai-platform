# Async Job Delivery Pattern / Playbook v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: ASYNC_JOB_DELIVERY_PATTERN_PLAYBOOK_V1_ACCEPTED

Branch: feature/async-job-delivery-pattern-playbook-v1

Source baseline: 71b14ea Merge feature/daily-coach-async-approved-preview-bridge-qa-v1

## Scope

Created a reusable async job delivery playbook from the accepted Daily Coach async provider/runtime/preview path.

This milestone is docs/pattern only.

## Delivered

- `docs/project_memory/patterns/async_job_delivery_pattern_v1.md`
- canonical async lifecycle guidance
- minimum data model and persistence concepts
- backend service shell pattern
- Developer Mode inspection requirement
- provider runtime pattern
- parser/schema/validator/fallback expectations
- approved preview bridge pattern
- feature flag and environment isolation strategy
- normal UI metadata boundary
- Developer Mode diagnostic boundary
- QA ownership and milestone pattern
- standard pass/fail criteria
- reusable milestone templates
- Daily Coach async case study
- lstop/lrestart/app CRLF issue recorded as backlog only

## Non-goals confirmed

- No runtime behavior changed.
- No provider behavior changed.
- No normal Today behavior changed.
- No Streamlit behavior changed.
- No new async job implemented.
- No worker / queue / scheduler / polling implemented.
- No lstop/lrestart/app tooling behavior modified.
- No qwen3 or qwen3:32b promotion.
- No Codex used by default.
