# Coach Voice Contract Tightening v1 Review

Status: IMPLEMENTED / PENDING QA

Implementation status: `COACH_VOICE_CONTRACT_TIGHTENING_V1_IMPLEMENTED_PENDING_QA`

## Decision pending

Coach Voice Contract Tightening v1 is ready for Architecture/QA review.

The implementation improves prompt/schema packaging for the offline coach voice bakeoff while preserving strict backend-owned truth boundaries and production isolation.

## Scope reviewed

Changed files are limited to the offline bakeoff harness, bakeoff tests, and project-memory documentation:

- `services/coach_voice_bakeoff_service.py`
- `tools/coach_voice_bakeoff.py`
- `tests/test_coach_voice_bakeoff_service.py`
- `docs/project_memory/milestones/coach_voice_contract_tightening_v1.md`
- `docs/project_memory/reviews/coach_voice_contract_tightening_v1.md`
- `docs/project_memory/runtime_qa/coach_voice_contract_tightening_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

No product UI, report integration, production provider path, food catalog, exercise catalog, workout generation, or nutrition formula file is changed.

## Accepted implementation characteristics

The tightened prompt now:

- uses plain instructions instead of showing raw JSON Schema metadata
- clearly separates output contract, example answer format, approved context, approved facts, and forbidden claims
- explicitly says not to return the schema
- explicitly forbids schema-echo keys such as `type`, `properties`, `required`, `items`, and `additionalProperties`
- repeats the exact backend-approved focus requirement
- tells the model to copy exact approved fact strings only
- keeps the required output keys unchanged

The report now includes model-level summary metrics and failure categories in addition to the context matrix.

## Validation expectations

Required local checks:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
.\.venv\Scripts\python.exe -m pytest tests\test_coach_voice_bakeoff_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_daily_next_action_service.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_report_persistence_boundary.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_full_report_section_registry.py -q
```

Required bakeoff QA command:

```powershell
python tools\coach_voice_bakeoff.py --all-contexts --model qwen2.5:3b --model qwen3:8b --model qwen3:14b --model qwen3:30b-a3b --model qwen3:32b
```

`qwen3:32b` may be run separately if runtime is too long.

## Review criteria

Architecture should accept if:

- harness still runs cleanly
- validators remain strict
- no production paths changed
- qwen3:8b remains compatible or improves
- qwen3:32b remains compatible or improves
- at least one previously failing model improves, or failure reasons become clearer without loosening validation
- report artifacts clearly show model/context outcomes
- no model is promoted

## Safety position

This is not production integration.

Preserved boundaries:

- no model promotion
- qwen3 remains not approved
- direct_ollama remains opt-in only
- no Today integration
- no Streamlit integration
- no report integration
- no production provider path change
- no provider gate change
- no validator loosening
- no deterministic fallback change
- no food catalog change
- no exercise catalog change
- no workout generation change
- no nutrition formula change
- no Level 5 Training semantic change
- no Level 5 Nutrition semantic change

## Recommended next step

Run the all-context bakeoff QA matrix and document results in:

`docs/project_memory/runtime_qa/coach_voice_contract_tightening_v1.md`
