# Open Questions

## Async Job Delivery Pattern / Playbook v1

Current status:
Async Job Delivery Pattern / Playbook v1 is implemented and ready for Architecture review.

Open after acceptance:

- Should DevOps Tooling SSH Command Normalization v1 be prioritized next? Likely yes if lstop/lrestart/app friction continues.
- Should the next async job be selected using the playbook? Yes, after the playbook is accepted.
- Should future async jobs skip Developer Mode inspection? No, unless Architecture explicitly approves a deviation.
- Should future preview bridges call providers? No.

## Tooling backlog

lstop/lrestart/app are Windows PowerShell helper commands that SSH into Linux.

Known backlog:
Fix lstop/lrestart/app SSH command CRLF handling in `scripts/fitness_commands.ps1` so SSH command blocks are normalized to LF before execution.

This was recorded during the async provider/live QA path and is not fixed in the playbook milestone.

## Portfolio / LinkedIn / GitHub

Portfolio / LinkedIn / GitHub update remains deferred until a stable end-to-end persisted async workflow is ready to describe cleanly.
