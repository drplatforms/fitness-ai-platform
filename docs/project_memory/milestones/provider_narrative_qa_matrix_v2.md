# Provider Narrative QA Matrix v2

Status: IMPLEMENTED / READY FOR MANUAL MATRIX EXECUTION

Date: 2026-06-20

## Purpose

Characterize Daily Coach provider narrative behavior across local models before any same-session approved display bridge is retried.

This milestone is a QA and characterization milestone. It is not a provider promotion milestone and it adds no provider output to normal Today UI.

## Source baseline

This branch starts from accepted main after:

- Daily Coach Developer Preview Stabilization v1
- Daily Coach Provider Preview Contract Reliability v1
- Project Memory Alignment + North Star Architecture v1
- Future Architecture Ledger
- Premium Platform Blueprint

Provider Contract Reliability v1 proved that `qwen2.5:3b` can reach:

- `provider_attempted = true`
- `parse_success = true`
- `validation_success = true`
- `approved_narrative_returned = true`
- `fallback_used = false`

through the manual Developer Preview debug lane.

## Approved scope

This milestone may:

- add developer-only QA tooling for a provider narrative matrix
- run the existing debug route across local models
- collect sanitized parse/validation/fallback diagnostics
- record rough latency observations
- document model behavior and failure modes
- identify the safest bridge retry baseline
- update project memory

## Not approved

This milestone must not add:

- same-session approval
- an "Approve for this session" button
- provider narrative display in normal Today UI
- provider calls on normal Today page load
- provider default changes
- model promotion
- persistence
- schema changes
- report persistence
- cache tables
- RAG/vector/MoE/MCP implementation
- frontend rewrite scaffolding
- deployment infrastructure

## Tooling added

`tools/provider_narrative_qa_matrix.py`

This script probes the existing Daily Coach narrative preview debug route and generates sanitized JSON and Markdown matrix reports.

The script does not call Ollama directly. FastAPI remains responsible for provider access, validation, fallback, and sanitization.

## Recommended runtime command

Linux runtime with Windows Ollama:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate
export OLLAMA_BASE_URL=http://192.168.1.104:11434
export PYTHONPATH="$PWD"

python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Second terminal:

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

python tools/provider_narrative_qa_matrix.py \
  --base-url http://127.0.0.1:8000 \
  --user-id 102 \
  --timeout-seconds 240 \
  --model qwen2.5:3b \
  --model qwen2.5:7b \
  --model qwen3:8b \
  --model qwen3:14b \
  --model qwen3:32b \
  --model qwen3:30b-a3b \
  --json-out qa_artifacts/provider_narrative_qa_matrix_v2.json \
  --markdown-out docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md
```

Important operational note: Ollama runs on the Windows machine for Dustin's current setup. Linux runtime must use `OLLAMA_BASE_URL=http://192.168.1.104:11434` unless the Windows host IP changes.

## Result classifications

- `APPROVED_BASELINE`
- `APPROVED_PROBE`
- `SAFE_REJECTED_PARSE`
- `SAFE_REJECTED_VALIDATION`
- `PROVIDER_ERROR`
- `TIMEOUT`
- `NOT_RUN`
- `DO_NOT_USE_FOR_BRIDGE`

## Acceptance requirement

Before final acceptance, the generated sanitized matrix results must be reviewed and committed to:

`docs/project_memory/runtime_qa/provider_narrative_qa_matrix_v2_results.md`

`qa_artifacts/` output remains local-only and must not be committed.

## Boundary confirmation

- Provider preview remains manual/developer-gated.
- Normal Today remains deterministic.
- No provider/model promotion is made by this milestone.
- qwen3:32b remains a future premium voice candidate only.
- Same-session approval remains parked until Architecture accepts a bridge retry.
