# Backend Handoff Current — Future Feature & Technology Inventory v1

Recipient: Backend Development / Data Layer.

Current source of truth: `main` at `9d66514`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_9d66514_nutrition-actuals-provenance-confidence-model-v1.zip`.

Current project-memory milestone: Future Feature & Technology Inventory v1.

Status: docs/project-memory update complete / ready for Architecture review.

## Backend relevance

This milestone does not assign backend implementation work.

It records future product and technology ideas so future backend milestones can be scoped cleanly.

Backend should treat the inventory as a north-star reference only until Architecture authorizes a specific implementation milestone.

## Current accepted backend nutrition capability

- canonical food search;
- serving-unit discovery;
- serving-unit logging;
- food_entries actuals bridge;
- serving-unit provenance metadata;
- actuals provenance/confidence interpretation;
- Target-vs-Actual compatibility.

## Ideas relevant to future Backend work

Future Backend candidates captured in inventory include:

- deterministic Daily Command Center data contract;
- meal planning / meal prep services;
- AI meal candidate validation contracts;
- food scanning extraction validation;
- barcode/catalog lookup boundaries;
- What-If simulator deterministic core;
- coach memory service;
- actuals confidence/provenance integration;
- adaptive training services;
- background job design;
- provider adapter registry;
- RAG/education retrieval boundaries;
- observability and QA artifact generation.

## Non-authorization

Do not start implementing any inventory item from this handoff alone.

Future implementation still requires a scoped Architecture handoff and acceptance criteria.

## Historical command/runtime anchors — reference-only

Local Command Menu App Runtime Correction v1 remains the accepted command-menu correction milestone.

`app` restarts Linux FastAPI + Streamlit through SSH.

`wapp` remains Windows-local only.

No backend app runtime code changed.
