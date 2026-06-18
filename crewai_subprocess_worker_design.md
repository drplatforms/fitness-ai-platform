# CrewAI Subprocess Worker Design

## Purpose

This document defines the v1 design for running CrewAI candidate recommendation generation in an isolated subprocess.

This is a design document only. It does not implement the subprocess worker, queueing, persistence, meal planning, workout planning, or a full report rewrite.

The goal is to preserve CrewAI as a grounded recommendation engine while keeping the FastAPI parent process stable. The parent process remains the source of truth and must own timeout enforcement, validation, approval, fallback, and rendering.

## Background

The accepted CrewAI runtime strategy is that same-process hard timeouts around CrewAI must not be retried. A prior same-process timeout experiment caused CrewAI/OpenAI runtime instability and CrewAI event bus warnings.

Future hard timeout behavior should be enforced outside the FastAPI process. The first recommended implementation path is a subprocess worker.

## Proposed worker entry point

The future worker entry point should be:

```powershell
python -m workers.crewai_candidate_worker
```

The worker should be invoked by the FastAPI parent process as a child process. The parent should send a request envelope to the worker through `stdin`, capture `stdout` and `stderr`, and enforce timeout at the subprocess boundary.

The worker module does not exist yet. This milestone only defines the intended design and contracts.

## High-level flow

```text
FastAPI parent process
→ build UserHealthState
→ build NutritionTargets
→ build TrainingConstraints
→ build RecommendationContext
→ serialize worker input envelope JSON
→ launch workers.crewai_candidate_worker subprocess
→ send request envelope through stdin
→ enforce subprocess timeout
→ capture stdout/stderr/exit code
→ parse worker output envelope
→ parse CandidateActionPlan JSON
→ validate candidate
→ approve or deterministic fallback
→ populate runtime metadata
→ render ApprovedActionPlan deterministically
```

CrewAI remains a candidate generator only. It must not render reports or produce user-facing markdown.

## Parent process responsibilities

The FastAPI parent process owns all trusted application behavior.

It must:

1. Build `RecommendationContext` JSON from trusted backend state.
2. Launch the subprocess worker.
3. Pass only the approved worker input envelope through `stdin`.
4. Enforce timeout using subprocess controls.
5. Capture `stdout`, `stderr`, and worker exit code.
6. Parse the worker output envelope.
7. Extract and parse `CandidateActionPlan` JSON.
8. Validate candidate schema and content.
9. Enforce nutrition target display/approval flags.
10. Enforce training constraints.
11. Enforce scenario-specific recommendation safety rules.
12. Convert valid candidates to `ApprovedActionPlan`.
13. Use deterministic fallback on timeout, worker failure, malformed output, or validation failure.
14. Populate runtime metadata.
15. Render only `ApprovedActionPlan` output.

The parent process must never render raw CrewAI output directly.

## Worker responsibilities

The subprocess worker should be intentionally small and replaceable.

It must:

1. Read one request envelope JSON object from `stdin`.
2. Validate basic request-envelope structure.
3. Build/run the CrewAI candidate generation task.
4. Return a simple output envelope to `stdout`.
5. Put diagnostics on `stderr` only.
6. Return `CandidateActionPlan` JSON only inside the output envelope.
7. Exit with a documented code.

The worker must not:

- query the application database
- build user health state
- approve recommendations
- persist output
- render final reports
- return markdown as final output
- write user-facing content outside the `CandidateActionPlan` fields
- bypass parent validation

## Input envelope

The parent should send a single JSON object to worker `stdin`.

Required fields:

```json
{
  "request_id": "uuid-or-trace-id",
  "recommendation_context": {},
  "model": "ollama/qwen3:8b",
  "ollama_base_url": "http://localhost:11434"
}
```

### Field definitions

- `request_id`: parent-generated identifier used for runtime metadata and log correlation
- `recommendation_context`: LLM-safe `RecommendationContext` JSON constructed by the parent
- `model`: CrewAI/Ollama model identifier
- `ollama_base_url`: local Ollama base URL

### Context safety requirements

The parent should send only LLM-safe context. Hidden or unapproved target values should not be included.

Examples:

- do not send calorie target values when `allow_calorie_targets` is false
- do not send carbohydrate target values when `allow_carbohydrate_targets` is false
- do not send fat target values when `allow_fat_targets` is false
- send protein targets only when `allow_protein_targets` is true
- include `nutrition_display_message` when nutrition confidence is limited
- include training constraints as approved boundaries
- avoid internal implementation details that are not needed for candidate generation

The worker should treat this context as the full approved context. It should not try to reconstruct or expand it.

## Output envelope

The worker should write exactly one JSON object to `stdout`.

### Successful output

```json
{
  "success": true,
  "candidate_action_plan": {
    "daily_coaching_recommendation": "...",
    "workout_recommendation": "...",
    "nutrition_action": "...",
    "rationale": "...",
    "confidence": "Low"
  }
}
```

### Failure output

```json
{
  "success": false,
  "error_code": "provider_exception",
  "message": "Short sanitized error message."
}
```

### Output rules

- `stdout` should contain only the output envelope JSON.
- Diagnostics should go to `stderr`, not `stdout`.
- `candidate_action_plan` must be JSON-compatible data, not markdown.
- Parent validation still treats the candidate as untrusted.
- The worker should not include stack traces, full raw model output, or sensitive context in the output envelope.

## Exit code policy

The worker should use the following exit codes:

| Exit code | Meaning |
|---:|---|
| 0 | Completed and wrote an output envelope to stdout |
| 1 | Provider exception |
| 2 | Invalid input |
| 3 | Provider returned invalid or non-string output |

A non-zero exit code should always cause the parent to use deterministic fallback.

The parent should not rely only on exit code. It should also validate that `stdout` contains a parseable and well-formed output envelope.

## Parent fallback mapping

The parent should map subprocess outcomes to runtime fallback reasons.

| Parent-observed outcome | Fallback reason |
|---|---|
| Subprocess timeout | `worker_timeout` |
| Non-zero exit code | `worker_exit_error` |
| Worker envelope cannot be parsed | `malformed_json` |
| Worker envelope missing required fields | `schema_mismatch` |
| Worker reports provider exception | `worker_exception` or `provider_exception` |
| Worker returns invalid/non-string provider output | `provider_non_string_output` |
| Candidate confidence is invalid | `invalid_confidence` |
| Candidate content fails validation | `validation_failure` |

Any fallback should produce a safe deterministic `ApprovedActionPlan`.

## Runtime metadata additions

The future subprocess implementation should extend internal runtime metadata with worker-specific fields.

Recommended additions:

- `worker_elapsed_ms`
- `worker_exit_code`
- `worker_timeout_used`
- `worker_stderr_preview`
- `worker_request_id`

Metadata should remain internal/debug-only. It should not be added to `ApprovedActionPlan` and should not appear in normal user-facing recommendation output.

### `worker_stderr_preview`

The parent may store a short sanitized `stderr` preview for debugging.

Recommended constraints:

- truncate to a small fixed length
- avoid full stack traces by default
- avoid full raw model output
- avoid full health state or full recommendation context
- include enough information to understand worker failure type

## Future provider toggle

The future implementation should add a new provider value:

```env
RECOMMENDATION_CANDIDATE_PROVIDER=crewai_subprocess
```

Recommended provider behavior:

| Provider value | Behavior |
|---|---|
| `deterministic` | Use deterministic candidate generation |
| `crewai` | Existing same-process CrewAI candidate path for manual runtime QA only |
| `crewai_subprocess` | Use isolated subprocess worker path |
| invalid/missing | Fall back to deterministic |

Deterministic should remain the default.

## Timeout behavior

The parent should enforce timeout at the subprocess boundary.

Suggested future env var:

```env
RECOMMENDATION_CANDIDATE_WORKER_TIMEOUT_SECONDS=45
```

On timeout, the parent should:

1. terminate or kill the subprocess
2. capture timeout metadata
3. avoid retrying inside the same request unless a later architecture decision allows it
4. use deterministic fallback
5. keep FastAPI process healthy

The parent should not attempt to cancel CrewAI work inside the worker process from within CrewAI. Process termination is the isolation boundary.

## Logging policy

Parent logs should include structured runtime information:

- provider configured
- provider selected
- request id
- scenario
- worker elapsed time
- worker exit code
- timeout used
- fallback used
- fallback reason
- validation errors

Worker logs should go to `stderr` and should be concise.

Do not log by default:

- full raw CrewAI output
- full health state
- full recommendation context
- sensitive user data beyond the minimum needed for debugging

## Testing strategy

Automated tests must never call live CrewAI/Ollama.

Future tests should use fake subprocess behavior:

1. fake subprocess valid output
2. fake subprocess malformed output
3. fake subprocess non-zero exit
4. fake subprocess timeout
5. fake unsafe candidate
6. fake provider exception envelope
7. fake invalid input envelope

Suggested testing techniques:

- monkeypatch `subprocess.run`
- return fake `CompletedProcess` objects
- raise `subprocess.TimeoutExpired`
- assert fallback metadata
- assert stable `/recommendations/daily/{user_id}` response shape
- assert debug endpoint exposes worker metadata only in debug output

## Non-goals

This design does not implement:

- subprocess worker module
- queue-backed worker
- durable job table
- `ApprovedActionPlan` persistence
- full report rewrite
- meal-plan engine
- workout-plan engine
- same-process timeout retry
- Streamlit debug UI

## Recommended first implementation slice

When implementation begins, keep the slice small:

1. Add `workers/crewai_candidate_worker.py`.
2. Add parent subprocess runner service function.
3. Add provider value `crewai_subprocess`.
4. Add worker metadata fields.
5. Add fake-subprocess tests.
6. Keep deterministic default.
7. Keep normal `/recommendations/daily/{user_id}` response unchanged.

Do not integrate queues or persistence in the first subprocess milestone.
