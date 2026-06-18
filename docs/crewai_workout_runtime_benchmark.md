# CrewAI Workout Runtime Benchmark Log

Purpose:
Track actual runtime results for CrewAI workout candidate generation through:
GET /workout-plans/preview/102/debug

Rules:
- Deterministic remains default.
- CrewAI is debug-only.
- Do not relax parser.
- Do not test other users until user 102 is practical.

## Result Template

### YYYY-MM-DD — MODEL_NAME

Environment:
- WORKOUT_CANDIDATE_PROVIDER=
- CREWAI_WORKOUT_MODEL=
- OLLAMA_BASE_URL=
- CREWAI_WORKOUT_DISABLE_THINKING=
- CREWAI_WORKOUT_JSON_RESPONSE_FORMAT=

Command:
```bash
curl -s -w "\nTotal time: %{time_total}s\n" \
  -o /tmp/workout_debug_102.json \
  http://127.0.0.1:8000/workout-plans/preview/102/debug



  ```markdown
  ## 2026-05-27 — qwen3:8b

  - elapsed time: 1135s
  - final_plan_source: deterministic_fallback
  - fallback_used: true
  - fallback_reason: invalid_confidence
  - candidate_parse_status: failed
  - candidate_validation_status: not_attempted
  - raw_output_length: 2328
  - markdown_wrapper_detected: false
  - raw_output_preview_truncated: returned schema-invalid workout fields like workout_id, user_id, workout_date, name, reps, rir_target, equipment

  Verdict:
  FAIL — reachable, no-think improved, but too slow and schema-invalid.


  ## 2026-05-27 — qwen2.5:3b

  - elapsed time: 159.78s
  - final_plan_source: deterministic_fallback
  - fallback_used: true
  - fallback_reason: schema_mismatch
  - candidate_parse_status: failed
  - candidate_validation_status: not_attempted
  - raw_output_length: 1936
  - markdown_wrapper_detected: false
  - raw_output_preview_truncated: returned context-like JSON with avg_rir, confidence, movement_pattern_targets, primary_goal

  Verdict:
  FAIL / PARTIAL — much faster than qwen3:8b, but still too slow and schema-invalid.

  ## 2026-05-27 — llama3.2:3b

  - elapsed time: 6.94s
  - final_plan_source: deterministic_fallback
  - fallback_used: true
  - fallback_reason: provider_exception
  - candidate_parse_status: not_attempted
  - candidate_validation_status: not_attempted
  - validation_errors: ConnectionError
  - raw_output_length: null
  - markdown_wrapper_detected: false
  - raw_output_preview_truncated: null

  Verdict:
  INVALID TRIAL — provider/runtime/model availability issue. Confirm model is pulled and reachable before counting.

   ## 2026-05-28 — gemma3:4b

  - elapsed time: 5 minutes
  - final_plan_source: deterministic_fallback
  - fallback_used: true
  - fallback_reason: malformed JSON
  - candidate_parse_status: failed
  - candidate_validation_status: not_attempted
  - validation_errors: Candidate workout output must be raw JSON, not markdown
  - raw_output_length: 5945
  - markdown_wrapper_detected: true
  - raw_output_preview_truncated: null

  Verdict:
  FAIL - Model provided malformed JSON, but fell back to deterministic as intended
