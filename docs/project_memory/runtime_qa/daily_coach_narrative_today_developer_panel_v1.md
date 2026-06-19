# Daily Coach Narrative Today Developer Panel v1 Runtime QA

Status: `PENDING_QA`

## Required users

- 101
- 102
- 105

## Manual Streamlit QA checklist

### 1. Normal Today view boundary

Expected:

- Launch Streamlit normally.
- Confirm normal Today view is unchanged when Developer Mode is off.
- Daily Coach Narrative Developer Preview panel is hidden.
- No provider call happens automatically.

### 2. Deterministic fallback lane

Expected:

- Enable Developer Mode.
- Open `Developer Preview: Daily Coach Narrative`.
- Confirm deterministic fallback appears.
- Select `Deterministic fallback`.
- Click manual preview button.
- Confirm fallback remains shown.
- Confirm public-safe status includes provider_attempted=false and fallback_used=true.

### 3. qwen3:8b fast preview lane

Expected:

- Select `Fast preview: qwen3:8b`.
- Click manual preview button.
- Confirm provider is attempted only after click.
- If validation passes, approved narrative appears.
- If validation fails or provider fails, fallback remains.
- No rejected/raw provider text is shown.

### 4. qwen3:32b premium preview lane

Expected:

- Select `Premium preview: qwen3:32b`.
- Confirm warning is displayed:
  `Premium preview may take several minutes. The deterministic fallback remains available while generation runs.`
- Click manual preview button only when intentionally testing the slow lane.
- Approved output appears only after backend validation passes.
- Timeout/failure keeps fallback visible.
- No stack trace or raw exception is displayed.

### 5. qwen2.5:3b baseline/regression lane

Expected:

- Select `Baseline/regression: qwen2.5:3b`.
- Click manual preview button.
- Approved output appears only if backend validation passes.
- Meta/process/internal language remains rejected by backend validation.
- Fallback remains if rejected.

## Leakage review

Confirm the panel does not display:

- rejected provider text
- raw model output
- raw prompts
- raw provider payloads
- raw model-facing schema
- raw validation internals
- raw stack traces
- provider exception internals
- hidden/internal architecture language

## Runtime status fields to inspect

Public-safe status may include:

- selected provider
- selected model
- provider attempted
- parse success
- validation success
- fallback used
- fallback reason
- latency ms

## Expected QA result

`DAILY_COACH_NARRATIVE_TODAY_DEVELOPER_PANEL_V1_QA_PASS`

or, if provider model results are mixed but the panel boundaries hold:

`DAILY_COACH_NARRATIVE_TODAY_DEVELOPER_PANEL_V1_PARTIAL_PASS_SAFE_BOUNDARY`
