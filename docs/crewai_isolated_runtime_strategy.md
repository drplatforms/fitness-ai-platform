# CrewAI Isolated Runtime Strategy

## Purpose

This document defines the future safe runtime boundary for CrewAI execution in the AI Health Coach project.

The goal is to preserve CrewAI as a grounded recommendation engine while protecting the FastAPI process from CrewAI/OpenAI runtime instability, long-running calls, and hard-timeout side effects.

This is a design document only. It does not implement subprocess execution, queueing, persistence, or a separate service.

## Current decision

Do not run hard timeout or forced cancellation logic around CrewAI inside the FastAPI process.

The previous same-process timeout experiment showed that cancelling or shutting down CrewAI execution inside the app process can leave CrewAI/OpenAI internals or the CrewAI event bus in an unhealthy state.

The safe current policy remains:

1. Deterministic recommendation generation is the default.
2. CrewAI recommendation generation is opt-in/manual runtime QA only.
3. CrewAI output must stay behind the `CandidateActionPlan` JSON boundary.
4. Backend parsing, schema validation, recommendation validation, and deterministic fallback remain mandatory.
5. `ApprovedActionPlan` remains the only renderable recommendation contract.
6. FastAPI must never render CrewAI raw output directly.

## Target isolated execution flow

Future CrewAI work should run outside the main FastAPI process.

The target flow is:

```text
FastAPI parent process
→ build UserHealthState
→ build NutritionTargets
→ build TrainingConstraints
→ build RecommendationContext
→ serialize RecommendationContext JSON
→ send JSON to isolated CrewAI worker
→ worker returns CandidateActionPlan JSON only
→ parent parses CandidateActionPlan JSON
→ parent validates candidate
→ parent approves or deterministically falls back
→ parent renders ApprovedActionPlan deterministically
```

CrewAI should never return markdown, final reports, Streamlit-ready content, or raw prose intended for direct rendering.

## Input contract

The isolated CrewAI worker should receive only the approved recommendation context needed for candidate generation.

Input:

```text
RecommendationContext JSON
```

The context should be LLM-safe and should not expose hidden or unapproved target values. For example:

- do not expose calorie targets when `allow_calorie_targets` is false
- do not expose carbohydrate targets when `allow_carbohydrate_targets` is false
- do not expose fat targets when `allow_fat_targets` is false
- expose protein targets only when `allow_protein_targets` is true
- include `nutrition_display_message` when nutrition confidence is limited
- include training constraints and scenario context only as approved coaching boundaries

The parent process owns context construction. The worker should not query the database directly in v1.

## Output contract

The isolated CrewAI worker must return raw `CandidateActionPlan` JSON only.

Required output fields:

```json
{
  "daily_coaching_recommendation": "...",
  "workout_recommendation": "...",
  "nutrition_action": "...",
  "rationale": "...",
  "confidence": "Low | Moderate | High"
}
```

Output rules:

- first character should be `{`
- last character should be `}`
- no markdown
- no code fences
- no commentary
- no extra fields
- no missing fields
- no final report sections
- no internal/debug terms
- no scenario changes
- no invented nutrition targets
- no contradiction of training constraints

The parent process treats all worker output as untrusted until parsed and validated.

## Parent-process responsibilities

The FastAPI parent process remains the source of truth.

It must:

1. Build factual and deterministic state:
   - `UserHealthState`
   - `NutritionTargets`
   - `TrainingConstraints`
   - `RecommendationContext`
2. Launch or call the isolated worker.
3. Enforce timeout at the process/request boundary.
4. Parse worker output.
5. Validate candidate schema and content.
6. Enforce scenario-specific safety rules.
7. Enforce target display/approval flags.
8. Convert valid candidates to `ApprovedActionPlan`.
9. Fall back deterministically on any failure.
10. Render only approved plans.

The parent must not allow a valid-looking CrewAI response to bypass backend validation.

## Worker responsibilities

The isolated worker should be small and replaceable.

It should:

1. Accept `RecommendationContext` JSON.
2. Run CrewAI candidate generation.
3. Return raw `CandidateActionPlan` JSON only.
4. Return a non-zero exit code or structured error if it cannot produce output.
5. Avoid direct database writes.
6. Avoid rendering final reports.
7. Avoid persistence of approved plans.

The worker may log local runtime diagnostics, but it must not become the source of truth for recommendation approval.

## Timeout and failure behavior

Timeouts should be enforced outside the CrewAI process.

If the isolated worker exceeds the configured timeout, the parent process should:

1. terminate the worker process or abandon the worker request
2. record runtime metadata
3. use deterministic fallback
4. return a safe `ApprovedActionPlan`

Recommended fallback reasons:

- `worker_timeout`
- `worker_exit_error`
- `worker_exception`
- `provider_exception`
- `provider_non_string_output`
- `malformed_json`
- `schema_mismatch`
- `invalid_confidence`
- `validation_failure`

The parent process should remain healthy after any worker timeout or failure.

## Recommended first implementation path: subprocess worker

The first future implementation should use subprocess isolation before introducing queues or services.

Suggested v1 approach:

```text
FastAPI
→ subprocess.run([...], input=context_json, timeout=seconds, capture_output=True)
→ parse stdout as CandidateActionPlan JSON
→ fallback on timeout/non-zero exit/invalid output
```

Advantages:

- simple local implementation
- no new infrastructure
- parent process can enforce a true hard timeout
- failed CrewAI runtime does not poison FastAPI
- easy to test with fake subprocess output

Tradeoffs:

- subprocess startup overhead
- no durable job tracking
- no horizontal scaling
- more limited observability than a queue-backed worker

This is acceptable for the first isolated runtime milestone because safety is more important than throughput.

## Future upgrade path

### Phase 1 — Subprocess worker

Create a small local worker module/script that accepts `RecommendationContext` JSON and returns `CandidateActionPlan` JSON.

Parent behavior:

- enforce subprocess timeout
- parse stdout
- validate candidate
- fallback on timeout/failure

### Phase 2 — Durable job table

Add persistent job metadata for recommendation/report generation.

Potential fields:

- job_id
- user_id
- provider
- status
- started_at
- completed_at
- elapsed_seconds
- fallback_used
- fallback_reason
- validation_errors
- approved_plan_id if persistence exists later

### Phase 3 — Queue-backed worker

Use a local or external queue for worker execution.

FastAPI enqueues work and polls job status. A worker process consumes jobs, runs CrewAI, and stores results or failure metadata.

Benefits:

- better resilience
- retries
- worker restartability
- non-blocking request handling
- easier runtime metrics

### Phase 4 — Separate recommendation service

Move CrewAI runtime into a separate service boundary.

FastAPI calls the service through HTTP/RPC with client-side timeout controls. If the service degrades, FastAPI falls back deterministically.

Benefits:

- clear runtime isolation
- independent deploy/restart
- separate scaling profile
- stronger failure containment

## Full report generation policy

FastAPI should not let CrewAI render final report text directly.

The full report should continue to be grounded by:

- deterministic state
- `CoachingDecision`
- `ApprovedActionPlan`
- report language validation
- deterministic rendering/fallback

If CrewAI contributes to the full report in the future, it should only produce structured candidate content that the parent process validates before rendering.

For now, CrewAI full report synthesis should remain out of scope unless it is moved behind an isolated worker boundary.

## Debug and observability expectations

The existing debug endpoint should remain the primary QA/developer inspection tool:

```text
GET /recommendations/daily/{user_id}/debug
```

Runtime metadata should remain separate from user-facing output.

Useful metadata for isolated execution:

- configured_provider
- selected_provider
- crewai_attempted
- fallback_used
- fallback_reason
- candidate_valid
- validation_errors
- candidate_parse_status
- candidate_validation_status
- final_plan_source
- raw_output_length
- raw_output_preview_truncated
- markdown_wrapper_detected
- worker_elapsed_ms
- worker_exit_code
- worker_timeout_used

Do not expose full raw model output in the normal UI.

## Testing strategy

Automated tests must not call live CrewAI/Ollama.

Future subprocess tests should use fake workers and monkeypatching to simulate:

- valid JSON output
- malformed JSON output
- markdown-wrapped output
- non-zero worker exit
- worker timeout
- unsafe candidate content
- confidence above context confidence
- hidden target leakage attempts

Required assertions:

- parent falls back deterministically on failure
- parent process remains healthy after timeout simulation
- normal endpoint response shape remains stable
- debug endpoint exposes runtime metadata
- `ApprovedActionPlan` remains free of debug metadata

## Recommended next implementation milestone

When implementation resumes, the recommended next milestone is:

```text
CrewAI Subprocess Candidate Worker v1
```

Suggested scope:

1. Add a worker script/module for candidate generation only.
2. Parent sends `RecommendationContext` JSON.
3. Worker returns `CandidateActionPlan` JSON only.
4. Parent enforces subprocess timeout.
5. Parent validates and approves or falls back.
6. Tests use fake subprocess output and never call live CrewAI.
7. Deterministic provider remains default.
8. CrewAI subprocess provider remains opt-in/manual until QA passes.

## Non-goals for this strategy milestone

Do not implement the following here:

- subprocess worker code
- queue-backed worker
- durable job table
- separate recommendation service
- ApprovedActionPlan persistence
- meal-plan engine
- workout-plan engine
- full report rewrite
- same-process hard timeout retry
