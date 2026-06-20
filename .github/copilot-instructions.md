# GitHub Copilot Instructions — AI Health Coach

AI Health Coach is a validation-first health coaching platform.

Keep suggestions narrow and consistent with existing service boundaries.

## Core rules

- Read `docs/project_memory/current_state.md` and `AGENTS.md` before larger edits.
- Backend owns facts, targets, constraints, validation, fallback, and persistence.
- AI/provider code may only explain backend-approved truth.
- Preserve deterministic fallback behavior.
- Preserve strict validators; do not loosen them casually.
- Do not change provider defaults or promote qwen3/local models.
- Do not invent endpoints, models, services, tables, or UI surfaces.
- Do not rewrite broad modules when a focused edit is enough.
- Do not add runtime agent orchestration, RAG, embeddings, scraping, app memory, or vector DBs unless explicitly scoped.
- Do not add Claude workflow files or Claude-specific commands.

## Safe coding behavior

- Prefer small helpers and focused tests.
- Match existing dataclass/model/service style.
- Keep public endpoints stable unless the milestone explicitly changes them.
- Keep raw provider output, prompts, payloads, validation internals, and stack traces out of normal UI/API responses.
- Never stage snapshots, patches, QA artifacts, runtime outputs, or local database files.

## Project memory update requirement

For meaningful feature or milestone work, update project memory before considering the branch complete. Do not imply provider/model promotion, persistence, same-session approval, or runtime behavior that has not been explicitly accepted.
