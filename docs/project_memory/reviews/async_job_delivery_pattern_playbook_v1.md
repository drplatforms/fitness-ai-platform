# Review — Async Job Delivery Pattern / Playbook v1

Review status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed accepted status: ASYNC_JOB_DELIVERY_PATTERN_PLAYBOOK_V1_ACCEPTED

## Result

Async Job Delivery Pattern / Playbook v1 captures the reusable async job architecture established by the Daily Coach async path.

The playbook covers lifecycle, persistence, service shell, Developer Mode inspection, provider runtime, parser/schema/validator/fallback, approved preview bridge, feature flags, normal UI metadata boundary, Developer Mode diagnostics, QA ownership, pass/fail criteria, milestone templates, and the Daily Coach async case study.

## Boundary confirmation

- Docs/pattern only.
- No runtime behavior changed.
- No provider behavior changed.
- No normal Today behavior changed.
- No Streamlit behavior changed.
- No new async job implemented.
- No worker added.
- No queue added.
- No scheduler added.
- No polling added.
- No qwen3/qwen3:32b promotion.
- lstop/lrestart/app CRLF issue recorded as backlog only.
- No Codex used by default.
- No snapshots committed.
- No qa_artifacts committed.

## Recommended next options

Option A:
DevOps Tooling SSH Command Normalization v1

Purpose:
Fix lstop/lrestart/app SSH command block CRLF handling in scripts/fitness_commands.ps1 so SSH command blocks are normalized to LF before execution.

Option B:
Next Async Job Candidate Selection v1

Purpose:
Choose the next async job using the new playbook instead of designing from scratch.
