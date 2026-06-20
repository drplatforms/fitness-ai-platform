# Project Memory Alignment + North Star Architecture v1

Status: IMPLEMENTED / READY FOR REVIEW after branch validation

## Goal

Restore project memory as the repo source of truth and add a future architecture ledger so future agents can maintain continuity without relying only on chat history.

## Scope

Docs and lightweight project-memory checks only.

## Implemented

- rewrote current accepted state summary
- reorganized open questions into active, parked, resolved, and reference-only sections
- updated AI/provider boundaries
- refreshed section registry summary
- refreshed product vision
- added future architecture ledger
- refreshed current handoff docs
- updated README current coverage notes
- added project memory update requirement
- recorded the failed same-session bridge as reference-only
- added project-memory checks for north-star and forbidden claims

## Non-goals preserved

- no runtime behavior changes
- no Streamlit UI behavior changes
- no FastAPI route changes
- no provider behavior changes
- no model promotion
- no same-session approval
- no persistence/schema/report changes
- no workout/nutrition/catalog behavior changes

## Definition of Done

Future meaningful milestones must update project memory before acceptance.
