# Development Architecture — ChatGPT Project Workflow v1

**Status:** Active development-workflow architecture
**Current accepted main:** `fc7ed70 main_merge-post-north-star-state-reconciliation-v1`

This ChatGPT Project is a seven-team development workspace, not a single chat with perfect memory.

## Windows / Linux Command Authority

Windows is the only machine used for commits, merges, pushes, and snapshots. Linux is pull/validate/runtime QA only and must never commit, merge, or push.

Every command block should be copy/paste ready with concrete branch names. Do not leave placeholders in user-facing commands.

## Core Rule

Repo docs are canonical. Chat context is useful, but it is not the source of truth. When a chat disagrees with repo docs, Architecture must re-study current repo docs, latest handoff, and accepted snapshot before issuing scope.

## Seven Team Workspace

The visible team/chat lanes are Architecture, Backend Development, QA, Agent Engineering, Streamlit UI / UX, Portfolio Packaging, and DevOps & Tooling.

Project Memory is not a visible team lane. It is a repo continuity responsibility shared by every lane.

## Latest Snapshot Requirement For Docs Patches

Before Architecture creates any docs-only project-memory patch, it must confirm the latest accepted post-merge snapshot is available. If not, request a fresh snapshot first. Do not patch from stale chat context or older snapshots.

## Snapshot + Handoff Discipline

Before a milestone, Architecture identifies accepted baseline commit and snapshot; Backend starts from that baseline; QA validates scoped branch/artifacts; final handoff records branch, commit, files, validation, known drift, and docs updates.

Do not assume an older chat has the latest state.


## Architecture Docs-Only Patch Policy

Architecture may create or route docs-only project-memory patches when the change is limited to documentation, milestone state, workflow memory, handoffs, ADRs, reviews, or architecture plans. This streamlines state reconciliation without forcing a Backend implementation loop for every repo-doc update.

Architecture must not use this exception for runtime or implementation files. If a change touches services, models, API routes, Streamlit behavior, provider behavior, tests, database/schema behavior, or application tooling behavior, route it to Backend Development.

The canonical command/process reference for Backend patch flow and Architecture acceptance/merge flow is:

```text
docs/project_memory/architecture_backend_command_workflow_v1.md
```

## Custom GPT Boundary

A custom GPT is not authorized yet. Custom GPT evaluation can happen later only after repo docs are clean and stable, team routing is canonical, current-state docs are reliable, and project memory is not stale.

## Prompt Lab Boundary

Prompt Lab is an engineering workflow, not a production runtime feature. It supports controlled prompt experiments, provider/model comparisons, cost tracking, rollback, and artifact safety. It does not authorize endless same-lane provider tuning when source data/backend intelligence is the bottleneck.

## Current State

Post-North-Star State Reconciliation + Architecture/Backend Workflow Memory v1 was merged at `fc7ed70`. Workout Set Intelligence v1 remains the latest Backend Intelligence Foundation implementation slice at `123d115`. Provider voice iteration is paused. The current Architecture lane should proceed from the latest snapshot, project memory, and the north-star file. Recovery Intelligence v2 Architecture Planning v1 defines the next source-data design, and Recovery Intelligence v2 Model Contract v1 is the next recommended Backend slice after Architecture accepts that plan.


## Platform North Star Reference

The canonical long-term platform vision and future technology stack lives in:

```text
docs/project_memory/architecture/platform_north_star_and_future_stack.md
```

Read it before making future-stack, SaaS, RAG, vector, agent, model-routing, or product-platform decisions.
