# Nutrition Full Report Opt-In Integration v1

Branch: `feature/training-evidence-claim-service`

Status: Implemented / local validation complete / pending Architecture review

Date/commit: Unknown / verify with git log.

## Problem

Nutrition had a proven Level 4 section-only opt-in provider path, but it was not available inside async/full-report generation. Architecture approved a narrow full-report integration step behind explicit gates, while preserving deterministic default behavior and avoiding Level 5 promotion before runtime QA.

## What changed

- Added a full-report Nutrition integration gate:
  - `AI_HEALTH_REPORT_NUTRITION_FULL_REPORT_INTEGRATION_ENABLED=false` by default.
- Preserved existing section provider gates:
  - `AI_HEALTH_REPORT_NUTRITION_SECTION_PROVIDER_ENABLED=true`
  - `NUTRITION_REPORT_SECTION_PROVIDER=direct_ollama`
- Added full-report Nutrition section building through the existing configured Nutrition provider service boundary.
- Rendered a distinct `Nutrition Report Section` separately from `Nutrition Target Display` when the full report has a Nutrition section result.
- Added Nutrition-prefixed safe full-report metadata.
- Added persistence allowlist entries for safe Nutrition-prefixed metadata.
- Added tests proving default deterministic behavior, strict gating, fake-generator opt-in behavior, fallback, safe persistence metadata, and coordinator-failure preservation.

## Files/modules touched

- `services/coordinator_service.py`
- `services/report_service.py`
- `services/nutrition_report_section_provider_service.py`
- `tests/test_nutrition_full_report_opt_in_integration.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/section_registry_summary.md`
- `docs/project_memory/milestones/nutrition_full_report_opt_in_integration_v1.md`

## Architecture decision

Nutrition may be wired into full-report generation only behind an explicit full-report integration gate. Nutrition remains Level 4 and is not Level 5 until runtime QA, persisted-history inspection, leakage checks, and Architecture approval pass.

Training remains the only Level 5 provider-integrated full-report section.

## Validation/tests

Required focused validation:

- `scripts/dev_commit_check.ps1 -Mode code`
- `pytest tests/test_nutrition_full_report_opt_in_integration.py -q`
- `pytest tests/test_nutrition_report_section_provider_service.py -q`
- `pytest tests/test_nutrition_report_section_boundary.py -q`
- `pytest tests/test_nutrition_provider_contract_parser.py -q`
- `pytest tests/test_nutrition_provider_contract_validation.py -q`
- `pytest tests/test_nutrition_provider_contract_fallback.py -q`
- `pytest tests/test_full_report_section_registry.py -q`
- `pytest tests/test_full_report_composition_boundary.py -q`
- `pytest tests/test_report_persistence_boundary.py -q`

## Runtime QA

Runtime QA is required after implementation before Architecture can accept full-report behavior.

Minimum recommended runtime QA:

1. deterministic/default full-report smoke for user 102/date 2026-06-14
2. provider section enabled but full-report integration disabled smoke
3. opt-in Nutrition full-report integration smoke for user 102/date 2026-06-14 with qwen2.5:3b
4. persisted-history inspection
5. exact-key leakage checks
6. users 101-105 sweep only after the minimum runtime QA passes and Architecture approves promotion consideration

## Known limitations

- Nutrition remains Level 4.
- Nutrition is not Level 5.
- Nutrition is not promoted as a provider-integrated full-report section until runtime QA and Architecture approval.
- qwen3 remains experimental only.
- This milestone does not add Streamlit, meal planning, new foods, RAG, embeddings, or agent orchestration.

## Next recommended step

Nutrition Full Report Opt-In Runtime QA v1.
