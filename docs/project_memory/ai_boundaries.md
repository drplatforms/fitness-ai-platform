# AI Boundaries

Last updated: 2026-06-20

## Core doctrine

Backend owns truth. AI explains truth.

The backend owns calculations, targets, logged values, recovery/training state, workout plans, catalogs, report registry, validation, fallback, persistence, and public-safe response shape.

AI/provider output may only phrase, explain, or summarize backend-approved context after parsing and validation.

## Default behavior

Deterministic fallback remains the default.

No provider is default-approved for normal Today page load, Daily Next Action selection, workout generation, nutrition calculations, catalog creation, or user memory.

## Current approved provider areas

### Training report section

Training Report Section has an opt-in direct-Ollama provider path with strict parser/validator gates and deterministic fallback.

### Nutrition report section

Nutrition Report Section is Level 5 provider-integrated on approved opt-in provider output. It preserves deterministic fallback, provider gates, sanitizer boundaries, and report-specific metadata.

### Daily Coach Narrative

Daily Coach Narrative provider lanes are manual/developer-gated preview and diagnostics only.

Accepted Daily Coach provider-adjacent work includes context builder, offline provider QA, provider contract tightening, developer preview endpoint, Today developer panel, and developer preview stabilization.

Not accepted:

- same-session approved display in normal Today UI
- provider narrative persistence
- async provider-generated Today narrative storage
- provider control over Daily Next Action

## Model status

- `qwen2.5:3b` is useful as a small local baseline for strict contract/JSON work.
- `qwen3:8b` is a promising practical voice candidate but not production-promoted.
- `qwen3:14b`, `qwen3:30b-a3b`, and `qwen3:32b` are experimental/developer-preview candidates only.
- `qwen3:32b` remains a future premium coach candidate only.

No model is allowed to promote itself.

Promotion requires Architecture acceptance, QA matrix evidence, deterministic fallback preservation, and explicit provider-boundary documentation.

## Normal UI restrictions

Normal user-facing UI must not show raw provider output, rejected provider output, prompts, full model context, stack traces, parser internals, validator internals, raw debug payloads, or hidden IDs that are not already part of safe UI convention.

Developer Mode may show sanitized diagnostics only.

## Persistence restrictions

Provider output may not be persisted unless a milestone explicitly approves the persistence boundary.

Daily Coach provider narrative persistence is not approved.

No provider cache table, database schema change, report persistence change, or file persistence is approved unless explicitly scoped.

## RAG/vector/MoE/MCP status

RAG, embeddings, vector databases, MoE routing, MCP/tool interfaces, and autonomous agents are future architecture ideas only.

They are recorded in `docs/project_memory/future_architecture_ledger.md` but are not implemented or authorized by that ledger.

## Failed bridge lesson

`feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is reference-only and not accepted.

It attempted same-session approval before the Daily Coach developer-preview and provider-preview diagnostics were stable. Future same-session approval work must come only after provider preview contract reliability is proven.
