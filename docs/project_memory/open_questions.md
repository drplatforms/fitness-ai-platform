# Open Questions — Future Feature & Technology Inventory v1

Current milestone: Future Feature & Technology Inventory v1.

Status: docs/project-memory update complete / ready for Architecture review.

## Current open question

Should Architecture accept `docs/project_memory/future_feature_technology_inventory_v1.md` as the durable future-facing product/technology/AI/platform inventory?

Requested final status:

`FUTURE_FEATURE_TECHNOLOGY_INVENTORY_V1_ACCEPTED`.

## Product / architecture questions preserved for future milestones

These are not implementation authorizations. They are future scoping questions:

1. Which future surface should become the first Daily Command Center milestone?
2. Should meal planning start as deterministic saved meals/templates before AI meal generation?
3. What food scanning path is safest first: barcode, nutrition label OCR, or photo-assisted logging?
4. Which actuals confidence/provenance fields should eventually appear in Target-vs-Actual or Nutrition Today Summary?
5. What is the first safe AI workout explanation surface?
6. What memory fields should be user-inspectable/editable first?
7. Which provider adapter should be evaluated first after local Ollama learning: OpenAI, Anthropic, Gemini, or more local models?
8. What is the minimum useful RAG education prototype that does not create truth?
9. When should PostgreSQL/Alembic become worth the migration cost?
10. What is the smallest mobile/PWA step that improves logging friction without a frontend rewrite?

## Current answer boundary

No future inventory item should be implemented until it receives a scoped Architecture handoff, owner, tests, QA classification, and acceptance path.

## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- Daily Coach Async Persistence Design v1
- qwen3:32b is research / future premium async candidate only
- deterministic fallback remains mandatory
- backend owns truth
- AI explains backend-approved truth
