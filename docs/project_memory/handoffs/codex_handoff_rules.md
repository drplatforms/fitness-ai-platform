# Codex / Coding Agent Handoff Rules

Codex-style coding helpers may be used only for scoped implementation work.

## Required reading

- `AGENTS.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/future_architecture_ledger.md`
- milestone-specific docs

## Rules

- Do not change architecture boundaries.
- Do not promote providers or models.
- Do not add same-session approval unless the milestone explicitly authorizes it.
- Do not add persistence/schema changes unless explicitly scoped.
- Do not add `CLAUDE.md` or Claude workflow files.
- Do not use Aider or Headroom unless reapproved.
- Do update project memory for meaningful changes.
- Keep patches narrow and validation commands explicit.
