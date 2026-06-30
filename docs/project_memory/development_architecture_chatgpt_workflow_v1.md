# Development Architecture — ChatGPT Project Workflow v1

**Status:** Active development-workflow architecture
**Current accepted main:** `23b5378 Merge daily coach fully free source-data lab evidence v1`

This ChatGPT Project is a seven-team development workspace, not a single chat with perfect memory.

## Core Rule

Repo docs are canonical. Chat context is useful, but it is not the source of truth. When a chat disagrees with repo docs, Architecture must re-study current repo docs, latest handoff, and accepted snapshot before issuing scope.

## Seven Team Workspace

The visible team/chat lanes are Architecture, Backend Development, QA, Agent Engineering, Streamlit UI / UX, Portfolio Packaging, and DevOps & Tooling.

Project Memory is not a visible team lane. It is a repo continuity responsibility shared by every lane.

## Snapshot + Handoff Discipline

Before a milestone, Architecture identifies accepted baseline commit and snapshot; Backend starts from that baseline; QA validates scoped branch/artifacts; final handoff records branch, commit, files, validation, known drift, and docs updates.

Do not assume an older chat has the latest state.

## Custom GPT Boundary

A custom GPT is not authorized yet. Custom GPT evaluation can happen later only after repo docs are clean and stable, team routing is canonical, current-state docs are reliable, and project memory is not stale.

## Prompt Lab Boundary

Prompt Lab is an engineering workflow, not a production runtime feature. It supports controlled prompt experiments, provider/model comparisons, cost tracking, rollback, and artifact safety. It does not authorize endless same-lane provider tuning when source data/backend intelligence is the bottleneck.

## Current State

Fully Free Source-Data Lab v1 was merged as developer-only evidence at `23b5378`. It was technically valid but not meaningfully better than v4. Provider voice iteration is paused. The next product center after docs cleanup is Backend Intelligence Foundation.
