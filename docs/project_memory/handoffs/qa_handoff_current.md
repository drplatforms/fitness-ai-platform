# QA Handoff Current

Milestone: Weekly Coach Summary Async Contracts + Data Model v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

QA focus:
- Verify valid weekly period can be constructed.
- Verify invalid/overlong weekly periods are rejected.
- Verify candidate/approved summary required user-facing sections are non-empty.
- Verify approved summary cannot be displayable when public_safe is false.
- Verify confidence/source/status values are constrained.
- Verify raw provider output, rejected provider output, full prompt, raw context, scratchpad, and chain-of-thought are not approved model fields.
- Verify no provider runtime, persistence schema, API endpoint, Streamlit UI, normal Today behavior, worker/queue/scheduler, or polling was added.
