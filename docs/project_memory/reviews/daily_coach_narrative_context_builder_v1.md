# Daily Coach Narrative Context Builder v1 Review

Status: IMPLEMENTED / PENDING QA

Implementation status: `DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_IMPLEMENTED_PENDING_QA`

## Decision requested

Review Daily Coach Narrative Context Builder v1 for acceptance.

This milestone builds the deterministic backend-approved context packet for future Daily Coach Narrative provider testing. It does not call a model and does not integrate model output into the product.

## Scope reviewed

Added:

- `models/daily_coach_narrative_models.py`
- `services/daily_coach_narrative_context_service.py`
- `tests/test_daily_coach_narrative_context_service.py`
- `docs/project_memory/milestones/daily_coach_narrative_context_builder_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_context_builder_v1.md`

Updated:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`
- `docs/project_memory/architecture/daily_coach_narrative_context_v1.md`

## Acceptance checklist

### Daily Next Action preservation

PASS expected.

The context builder preserves:

- `next_action_id`
- `next_action_title`
- `next_action_reason`
- `workflow_target`
- `priority`
- `severity`

`approved_focus` is exactly the Daily Next Action title.

### Approved facts

PASS expected.

Approved facts are explicit strings derived from Daily Next Action public fields and public-safe evidence only.

Examples:

- `Daily next action: Log a meal or snack`
- `Daily next action reason: Today's nutrition state is limited until more food data is logged.`
- `Workflow target: nutrition_quick_log`
- `Nutrition logging completeness: likely_incomplete`

### Approved limitations

PASS expected.

The builder emits limitations for missing recovery check-ins, limited nutrition confidence, incomplete nutrition logging, and missing workout preview context where applicable.

### Forbidden claims

PASS expected.

The context includes v1 forbidden claim categories covering:

- changed action
- changed workflow target
- invented foods
- invented exercises
- invented targets
- invented serving sizes
- meal plans
- medical/clinical claims
- unsupported fatigue/recovery/progression/consistency claims
- exercise substitutions
- unapproved internal metadata

### Fallback behavior

PASS expected.

Fallback wording is deterministic:

```text
{next_action_title}: {next_action_reason}
```

### Public-safe metadata

PASS expected.

The builder filters raw/debug/provider-style evidence keys and returns only public-safe source metadata.

### Model boundary

PASS expected.

No model call exists in this milestone. There is no qwen, Ollama, direct_ollama, or CrewAI invocation.

## Boundaries preserved

Preserved:

- no model promotion
- qwen3 remains not approved
- no Today integration
- no Streamlit integration
- no report integration
- no production provider path change
- no direct_ollama default change
- no validator loosening
- no deterministic fallback weakening
- no provider gate change
- no catalog changes
- no workout generation changes
- no nutrition formula changes
- no Training Level 5 or Nutrition Level 5 semantic changes

## Validation requested

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
.\.venv\Scripts\python.exe -m pytest tests\test_daily_coach_narrative_context_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_next_action_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_report_persistence_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
```

## Recommended Architecture decision

Accept as:

`DAILY_COACH_NARRATIVE_CONTEXT_BUILDER_V1_ACCEPTED`

Recommended next milestone:

`Daily Coach Narrative Offline Provider Runtime QA v1`
