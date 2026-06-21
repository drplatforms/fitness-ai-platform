# Provider Narrative QA Matrix v2 Results

Status: PENDING RUNTIME EXECUTION

Date: 2026-06-20

## Purpose

This document will hold sanitized runtime QA results for the Daily Coach manual provider preview lane.

It must be generated from the existing debug route by running:

```bash
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

## Boundary

This matrix is characterization only.

It does not:

- promote any model
- approve same-session display
- does not promote any model
- does not approve same-session display
- add provider output to normal Today UI
- persist provider narrative
- change provider defaults
- authorize qwen3:32b for production

Runtime result table will replace this pending document after manual QA execution.
