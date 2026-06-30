# Team Routing Contract — AI Health Coach / fitness_ai

**Status:** Active routing contract
**Current accepted main:** `23b5378 Merge daily coach fully free source-data lab evidence v1`
**Active milestone:** Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1

This document defines the visible team/chat lanes for the project. Do not invent additional visible teams unless Architecture updates this contract.

## Canonical Seven Team Lanes

1. Architecture
2. Backend Development
3. QA
4. Agent Engineering
5. Streamlit UI / UX
6. Portfolio Packaging
7. DevOps & Tooling

`Project Memory / All Future Agents` is not one of the seven visible team/chat lanes. It is a repo continuity concern that every team must respect.

## Routing Rules

### Architecture

Owns product/system architecture, sequencing, acceptance decisions, scope boundaries, roadmap discipline, milestone definition, and cross-team routing.

### Backend Development

Owns backend services, deterministic logic, data models, provider/service boundaries, API/persistence logic when authorized, tests for those layers, and repo-doc patches when Architecture routes docs work.

### QA

Owns validation evidence, runtime checks, artifact inspection, pass/fail classification, user-path validation, and clear QA return reports.

### Agent Engineering

Owns provider lab methods, future agent/orchestration planning, Prompt Lab support, model/tool workflow design, and model-evaluation mechanics after Architecture scopes them.

### Streamlit UI / UX

Owns Today/Workout/Nutrition UI, developer panels, user-facing layout, cards/tables/rendering, copy placement, visual hierarchy, and user-path polish.

### Portfolio Packaging

Owns GitHub/LinkedIn/resume/portfolio assets, screenshots, public project narrative, demo framing, and presentation packaging. This is a low-frequency lane, not core product architecture.

### DevOps & Tooling

Owns helper commands, command menu, environment setup, Windows/Linux workflow support, snapshots/tooling mechanics, runtime setup diagnostics, and local operational support. This is a narrow, low-frequency lane. Do not route general architecture, backend product logic, provider decisions, UI work, or roadmap ownership here.

## Required Handoff Behavior

Every team handoff must include current branch/baseline, accepted or requested status, affected files/artifacts, validation evidence expected, project-memory/docs impact, explicit non-goals, and next owner.

Project memory is a first-class continuity layer. Update current state, next milestone, open questions, project state, milestone docs, handoffs, README, and boundary docs whenever behavior, architecture, tests, UI, provider behavior, persistence, routing, or accepted status changes.
