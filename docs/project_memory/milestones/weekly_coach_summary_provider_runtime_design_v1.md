# Weekly Coach Summary Provider Runtime Design v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW
Branch: `feature/weekly-coach-summary-provider-runtime-design-v1`
Commit: pending
Snapshot: pending

## Purpose

Design the future Weekly Coach Summary provider runtime path using the accepted
backend-owned QA date-range context seam and the accepted provider lifecycle
policy.

This is a design milestone. It does not execute provider runtime, call qwen,
call Ollama for Weekly Coach Summary, reintroduce CrewAI, add public/default
display, or add automatic generation.

## Outputs

- provider runtime design doc
- provider input contract
- provider output JSON schema
- parser rules
- validator rules
- fallback rules
- persistence boundary
- Developer Mode-only manual preview design
- lifecycle policy integration
- voice/tone contract
- happy-path, low-data, and out-of-range scenarios
- future prototype test plan
- non-executing provider model/schema scaffolding

## Accepted prerequisites

- `0fd327d Restore weekly QA selected-range persistence controls`
- `be2f321 Add provider runtime resource lifecycle policy`

## Boundary

Backend tells the truth. Provider improves the voice. Validator decides what
survives. Deterministic fallback always works.
