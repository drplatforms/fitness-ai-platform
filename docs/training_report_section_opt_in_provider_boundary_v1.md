# Training Report Section Opt-In Provider Boundary v1

## Status

Implemented for backend review.

## Purpose

Formalize the training report section provider boundary without making direct Ollama the product default. Deterministic rendering remains the default and deterministic fallback remains the public-safe path whenever provider output is missing, invalid, or unsupported.

## Provider Modes

- `deterministic` — default provider. Does not call Ollama.
- `direct_ollama` — opt-in provider boundary. Uses the configured training report section model, defaulting to `ollama/qwen2.5:3b`.

Environment variables:

- `TRAINING_REPORT_SECTION_PROVIDER`
- `TRAINING_REPORT_SECTION_MODEL`
- `TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS`

## Boundary Flow

Approved backend training facts flow into the bounded training report section context. The direct Ollama provider may generate a candidate section only when approved quote context contains a required quote name, exact required fact anchors, and approved workout or exercise names.

Candidate output must pass:

- JSON parsing
- schema/shape conversion
- exact anchor validation
- approved training name validation
- approved claim validation
- coaching move validation
- placeholder/artifact rejection
- medical and unsupported-claim rejection

If any gate fails, the service returns the deterministic fallback section with structured runtime metadata.

## Public Content Rule

Raw provider output is not approved content. The public `ApprovedTrainingReportSection` contains only validated section fields and source. Raw output diagnostics stay in runtime metadata for debugging.

## Model Position

- `qwen2.5:3b` is the practical opt-in candidate based on the accepted longitudinal QA sweep.
- `qwen3:8b` remains experimental only.
- deterministic remains default.

## Non-Goals

This milestone does not integrate the provider into the full AI Health Report by default, promote qwen3, loosen validators, change Streamlit, change report persistence, add foods, add exercises, add meal planning, or add CrewAI changes.

## Runtime Acceptance Addendum � Service Boundary

Runtime date: 2026-06-16

Formal service-boundary runtime QA was executed through:

`build_configured_training_report_section_with_metadata(...)`

This confirms the provider boundary path, not only the spike CLI.

### qwen2.5:3b Service-Boundary Sweep

Environment:

- `TRAINING_REPORT_SECTION_PROVIDER=direct_ollama`
- `TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b`
- `TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=300`
- report date: `2026-06-14`
- users: `101, 102, 103, 104, 105`

Results:

| User | Source | Provider | Model | Attempted | Fallback | Validation | Errors | Anchors | Artifact Leaks | Raw/Public Leak |
|---:|---|---|---|---:|---:|---|---|---:|---:|---:|
| 101 | direct_ollama_approved | direct_ollama | qwen2.5:3b | true | false | approved | none | 3 / 2 | false | false |
| 102 | direct_ollama_approved | direct_ollama | qwen2.5:3b | true | false | approved | none | 3 / 2 | false | false |
| 103 | direct_ollama_approved | direct_ollama | qwen2.5:3b | true | false | approved | none | 3 / 2 | false | false |
| 104 | direct_ollama_approved | direct_ollama | qwen2.5:3b | true | false | approved | none | 3 / 2 | false | false |
| 105 | direct_ollama_approved | direct_ollama | qwen2.5:3b | true | false | approved | none | 3 / 2 | false | false |

Observed latency:

- user 101: 118617 ms
- user 102: 118512 ms
- user 103: 121813 ms
- user 104: 116681 ms
- user 105: 91598 ms

### Runtime Acceptance Decision

`Training Report Section Opt-In Provider Boundary v1` is runtime accepted if the deterministic-default smoke also confirms provider is not attempted when opt-in env vars are unset.

qwen2.5:3b remains the practical opt-in candidate.

Direct Ollama remains opt-in only.

Deterministic remains default and fallback.

qwen3 remains experimental only.

No validator loosening is recommended.
