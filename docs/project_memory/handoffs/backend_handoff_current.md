# Backend Handoff Current

Updated: 2026-06-21
Current milestone: Async Daily Coach Narrative Implementation Plan v1
Backend role: Future recipient only

## Backend Status

Backend should not implement async Daily Coach runtime yet.

Architecture has created the implementation plan that Backend may execute later after formal acceptance.

## Not Authorized Yet

Backend is not yet authorized to add:

- async runtime
- background worker
- queue
- scheduler
- DB schema changes
- provider cache table
- provider call on normal Today load
- qwen3 bridge eligibility
- model promotion
- normal UI async display

## Likely Next Backend-Executable Milestone

Daily Coach Async Contracts + Data Model v1

Likely scope when authorized:

- job status enum
- narrative job contract/model
- context identity/hash contract
- safe metadata shape
- tests

No provider runtime should be included in that first implementation milestone unless Architecture explicitly changes scope.
