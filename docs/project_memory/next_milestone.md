# Next Milestone

Current authorized milestone:
Weekly Coach Summary Async Contracts + Data Model v1

Status:
IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
WEEKLY_COACH_SUMMARY_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED

Purpose:
Define the contracts and data model for the selected Weekly Coach Summary Async Job before implementation begins.

Recommended next milestone after acceptance:
Weekly Coach Summary Async Service Shell / No Worker v1

Why:
The accepted async playbook recommends service shell before persistence, provider runtime, worker/queue/scheduler, or UI exposure.

Recommended next scope:

- deterministic service shell functions around accepted weekly summary contracts
- no persistence schema
- no provider runtime
- no API endpoint
- no Streamlit UI
- no worker / queue / scheduler / polling
- no automatic weekly generation

Still not authorized:

- Weekly Coach Summary persistence schema/service
- Weekly Coach Summary provider runtime
- normal Today provider execution
- provider execution on page load
- automatic async job generation
- worker / queue / scheduler / polling
- public/default weekly summary display
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
