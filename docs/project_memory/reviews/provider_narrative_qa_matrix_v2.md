# Provider Narrative QA Matrix v2 Review

Status: IMPLEMENTED / AWAITING RUNTIME MATRIX RESULTS

Date: 2026-06-20

## Review summary

Provider Narrative QA Matrix v2 adds developer-only matrix tooling and project-memory scaffolding for characterizing Daily Coach provider narrative behavior across local models.

The implementation does not change product runtime behavior. It adds a safe QA runner around the already accepted manual Daily Coach narrative preview debug route.

## Implementation reviewed

Added:

- `tools/provider_narrative_qa_matrix.py`
- `tests/test_provider_narrative_qa_matrix_v2.py`
- `docs/project_memory/milestones/provider_narrative_qa_matrix_v2.md`
- `docs/project_memory/reviews/provider_narrative_qa_matrix_v2.md`
- `docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md`

Updated:

- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Runtime matrix status

Pending execution on the Linux runtime with Windows Ollama configured through:

`OLLAMA_BASE_URL=http://192.168.1.104:11434`

The generated matrix results should be written to:

`docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md`

## Acceptance blocker

Do not accept this milestone until the runtime matrix results are present and reviewed.

The matrix should at minimum report the outcome for:

- `qwen2.5:3b`
- `qwen3:8b`
- `qwen3:14b`
- `qwen3:32b`

Optional if available:

- `qwen2.5:7b`
- `qwen3:30b-a3b`

## Boundary review

Confirmed by implementation:

- no same-session approval
- no "Approve for this session" button
- no provider narrative in normal Today UI
- no provider call on normal Today load
- no provider default change
- no model promotion
- no persistence
- no database schema changes
- no report persistence changes
- no Daily Next Action changes
- no nutrition changes
- no workout changes
- no catalog changes
- no RAG/vector/MoE/MCP implementation
- no frontend rewrite scaffolding
- no deployment infrastructure

## Provisional decision

Implementation is acceptable as matrix tooling and docs scaffolding.

Final milestone acceptance depends on completed runtime QA matrix evidence.
