# CrewAI Runtime Safety

## Current policy

The stable local/default runtime should use deterministic recommendation generation:

```env
RECOMMENDATION_CANDIDATE_PROVIDER=deterministic
```

CrewAI candidate generation remains available only as an explicit manual runtime QA mode:

```env
RECOMMENDATION_CANDIDATE_PROVIDER=crewai
CREWAI_RECOMMENDATION_MODEL=ollama/qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
```

Workout plan generation remains deterministic by default. The workout explanation provider may be tested with CrewAI because it explains an already-approved `ApprovedWorkoutPlan` and cannot change exercises, sets, reps, RIR, equipment, progression, or deload decisions.

```env
WORKOUT_CANDIDATE_PROVIDER=deterministic
WORKOUT_EXPLANATION_PROVIDER=deterministic
```

Do not enable CrewAI mode for normal local development, automated tests, or broad QA unless the specific goal is to inspect CrewAI runtime behavior.

## Why same-process hard timeouts were reverted

A same-process timeout/fallback experiment around CrewAI report generation and candidate generation was attempted and reverted.

Observed runtime failures included:

- `OpenAI API call failed: cannot schedule new futures after shutdown`
- OpenAI connection/time-out errors
- `CrewAIEventsBus` event pairing mismatch warnings
- `crew_kickoff_failed` events emitted with an empty scope stack

The conclusion is that hard-timeout/shutdown handling around CrewAI inside the same FastAPI Python process can poison CrewAI/OpenAI runtime state. Even when application-level fallback succeeds, the underlying event bus or executor state may become unreliable for later calls.

## Known unsafe pattern

Avoid wrapping `Crew.kickoff()` or CrewAI/OpenAI calls in same-process hard-timeout mechanisms that cancel or shut down executor threads.

Unsafe patterns include:

- running CrewAI inside a local `ThreadPoolExecutor` and cancelling the future on timeout
- shutting down an executor while CrewAI/OpenAI internals may still be using worker threads
- attempting to forcibly kill CrewAI work from inside the FastAPI process
- running full report CrewAI synthesis with same-process timeout controls

This app should not retry the reverted same-process hard-timeout design.

## Safe current behavior

The safe runtime posture is:

1. Deterministic recommendation generation is the default.
2. CrewAI candidate generation is opt-in/manual only.
3. CrewAI output must stay behind the `CandidateActionPlan` JSON boundary.
4. Backend parsing, schema validation, recommendation validation, and deterministic fallback remain mandatory.
5. `ApprovedActionPlan` remains the only renderable recommendation contract.
6. The debug endpoint should be used to inspect provider/fallback behavior:
   - `GET /recommendations/daily/{user_id}/debug`
7. Workout candidate generation remains deterministic by default.
8. Workout explanation CrewAI tests must stay behind the debug endpoint:
   - `GET /workout-plans/preview/{user_id}/explanation/debug`
9. No raw AI output should be exposed from normal workout preview endpoints.
10. Workout candidate and explanation parsers/validators must remain strict.

Normal QA should start in deterministic mode. CrewAI mode should be limited to targeted runtime experiments.

## CrewAI workout explanation runtime QA

Use this path only for manual debugging of explanation copy over an already-approved deterministic workout plan. The normal workout preview endpoint must remain stable and must not expose runtime metadata or raw model output.

Known-good split-runtime configuration for `qwen2.5:3b` through the CrewAI/LiteLLM/OpenAI-compatible Ollama path:

```env
WORKOUT_CANDIDATE_PROVIDER=deterministic
WORKOUT_EXPLANATION_PROVIDER=crewai
CREWAI_WORKOUT_MODEL=ollama/qwen2.5:3b
OLLAMA_BASE_URL=http://<WINDOWS_LAN_IP>:11434
CREWAI_WORKOUT_DISABLE_THINKING=false
CREWAI_WORKOUT_JSON_RESPONSE_FORMAT=true
```

Important provider notes:

- `CREWAI_WORKOUT_JSON_RESPONSE_FORMAT=true` uses `response_format={"type": "json_object"}` and is required for this provider path.
- For `qwen2.5:3b` through this CrewAI/LiteLLM/OpenAI-compatible path, keep `CREWAI_WORKOUT_DISABLE_THINKING=false`; passing the `think` kwarg can raise `TypeError: Completions.create() got an unexpected keyword argument 'think'`.
- Strict backend parsing and validation still determine whether a model explanation is approved.
- Invalid, malformed, unsafe, or provider-failed output must fall back to the deterministic explanation.
- The approved workout plan remains unchanged regardless of explanation-provider output.

Manual test endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/workout-plans/preview/102/explanation/debug
```

Best-case runtime metadata:

- `configured_provider: crewai`
- `selected_provider: crewai`
- `crewai_attempted: true`
- `candidate_parse_status: success`
- `candidate_validation_status: success`
- `final_explanation_source: crewai_approved`
- `fallback_used: false`

Safe fallback remains acceptable when `fallback_reason` is clear and the normal workout preview endpoint remains stable.

## Full report generation policy

Do not add same-process hard timeouts around full AI Health Report CrewAI synthesis.

Until an isolated execution boundary exists, full report generation should remain on the stable deterministic/validated path. If CrewAI is used for report-related work, it should be isolated from the FastAPI process or limited to explicit experiments.

## Future safe execution options

True hard timeout/fallback support should use an isolation boundary outside the main FastAPI process. Possible future options:

### 1. Subprocess worker

Run CrewAI in a subprocess and communicate via stdin/stdout, files, or a small IPC contract. The parent FastAPI process can terminate the subprocess if it exceeds a timeout without poisoning the parent process.

### 2. Separate local worker process

Run a separate local Python worker for CrewAI tasks. FastAPI submits a job and polls or receives a result. If the worker becomes unhealthy, restart only the worker.

### 3. Queue-backed worker

Use a queue-backed architecture where FastAPI enqueues recommendation/report jobs and a worker process consumes them. This enables retries, job metadata, timeouts, and worker restarts without blocking request handling.

### 4. Separate recommendation service

Move CrewAI runtime into a separate service boundary. FastAPI calls the service through HTTP/RPC with client-side request timeouts. If the service degrades, FastAPI can fall back deterministically.

## Recommended next testing process

For normal development and QA:

1. Set deterministic mode:
   ```powershell
   $env:RECOMMENDATION_CANDIDATE_PROVIDER="deterministic"
   $env:WORKOUT_CANDIDATE_PROVIDER="deterministic"
   $env:WORKOUT_EXPLANATION_PROVIDER="deterministic"
   ```
2. Restart FastAPI.
3. Run:
   ```powershell
   pytest
   ```
4. Validate the stable endpoint:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/recommendations/daily/105
   ```
5. Validate the debug endpoint:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/recommendations/daily/105/debug
   ```

For manual CrewAI candidate testing only:

1. Set CrewAI mode in the same terminal that starts FastAPI:
   ```powershell
   $env:RECOMMENDATION_CANDIDATE_PROVIDER="crewai"
   $env:CREWAI_RECOMMENDATION_MODEL="ollama/qwen3:8b"
   $env:OLLAMA_BASE_URL="http://localhost:11434"
   ```
2. Restart FastAPI.
3. Test the debug endpoint first:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/recommendations/daily/105/debug
   ```
4. Inspect runtime metadata:
   - `configured_provider`
   - `selected_provider`
   - `crewai_attempted`
   - `fallback_used`
   - `fallback_reason`
   - `candidate_parse_status`
   - `candidate_validation_status`
   - `final_plan_source`
   - `markdown_wrapper_detected`

If CrewAI/OpenAI runtime errors appear, stop FastAPI, switch back to deterministic mode, and restart from a clean process.

## Testing policy

Automated tests must not call live CrewAI/Ollama. Tests should use fake providers/monkeypatching and assert that:

- deterministic mode stays fast and stable
- CrewAI provider behavior can be simulated safely
- malformed, invalid, or unsafe candidates fall back deterministically
- debug metadata remains available without changing the stable user-facing endpoint response

## Current non-goals

Do not implement the following in this milestone:

- ApprovedActionPlan persistence
- meal-plan engine
- workout-plan engine
- Streamlit debug UI
- full report architecture rewrite
- same-process hard timeouts around CrewAI
