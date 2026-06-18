# ADR: AI Provider Validation Boundary

Status: Accepted

Date: Unknown / verify with git log

## Context

AI Health Coach needs clear boundaries so provider voice can improve user-facing copy without taking ownership of truth.

## Decision

Provider output may explain approved truth, but must be parsed, validated, and converted to approved content before rendering.

## Rationale

This preserves the product principle: backend owns truth, AI explains approved truth, validator enforces reality.

## Consequences

- Provider work must be sectionized and validated.
- Deterministic fallback remains required.
- Public/persisted reports must remain safe when providers or coordinators fail.

## Alternatives considered

- Letting a model write the whole report from raw context.
- Treating provider output as trusted.
- Moving faster by loosening validators.

These alternatives are rejected for now because they increase hallucination and product-quality risk.

## Validation

See relevant milestone summaries and runtime QA files under `docs/project_memory/`.

## Related files

- `docs/project_memory/current_state.md`
- `docs/project_memory/backend_truth_contract.md`
- `docs/project_memory/ai_boundaries.md`
- `docs/project_memory/section_registry_summary.md`

## Related milestones

See `docs/project_memory/milestones/`.
