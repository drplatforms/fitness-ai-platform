# Bounded Coach Voice Bakeoff v1

Status: IMPLEMENTED / PENDING QA

## Purpose

Bounded Coach Voice Bakeoff v1 creates an offline/backend-controlled evaluation harness for comparing local model coaching language against the same backend-approved context packs.

This milestone asks whether a local model can sound like a premium coach while staying inside approved truth boundaries.

## Scope

Implemented as an evaluation harness only:

- fixed backend-approved context packs
- strict JSON output contract
- parser and validator for candidate coach notes
- deterministic scoring dimensions
- local-only result/report generation
- command-line tool for model bakeoffs
- tests for schema parsing, forbidden claim detection, grounding, and score/report behavior

## Non-goals preserved

This milestone does not:

- integrate model output into Today
- replace Daily Next Action deterministic selection
- promote qwen3
- make qwen3 or direct_ollama default
- change provider gates
- loosen validators
- change Training or Nutrition Level 5 semantics
- add RAG, embeddings, scraping, or agents
- add meal planning
- create food or exercise suggestions through AI
- change food or exercise catalogs
- change workout generation
- change nutrition formulas
- expose raw model output in normal UI
- persist raw model output into report history

## Context packs

The harness includes fixed context packs for:

- user 101 recovery-limited conservative training
- user 102 Daily Next Action / log-food context
- user 105 data-quality-limited logging context
- user 102 nutrition target-vs-actual status
- user 102 workout preview context

The starter run should use the first three contexts.

## Required model candidates

Starter candidate set:

- qwen2.5:3b
- qwen3:8b
- qwen3:14b

Optional later candidates:

- qwen3:30b-a3b
- qwen3:32b

No model is promoted by this milestone.

## Expected status after QA

BOUNDED_COACH_VOICE_BAKEOFF_V1_ACCEPTED

Acceptance of the bakeoff means the harness and scorecard are accepted. It does not approve any model for production.
