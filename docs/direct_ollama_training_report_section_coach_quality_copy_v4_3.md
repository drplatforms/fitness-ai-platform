# Direct Ollama Training Report Section Coach-Quality Copy v4.3

## Status
Implemented as a spike-only style-safety pass after Claim-Safe Interpretation v4.2.

## Purpose
v4.2 proved that direct Ollama can produce structurally approved training report output with exact anchors and approved interpretation claims. Runtime QA also showed that approved output can still sound too much like a debug report, and that form/control wording such as `controlled execution` can slip through unless the validator treats it as an unsupported claim.

v4.3 keeps the v4.2 safety contract and adds a user-facing copy-quality layer. The goal is not to loosen validation or promote the provider. The goal is to make approved copy more coach-like while continuing to reject unsupported claims.

## Scope
This remains spike-only.

Included:

- approved coaching frames in the model-facing quote context
- prompt separation between required details, allowed interpretation claims, and approved coaching frames
- copy-quality validation for debug/internal wording
- stronger form/control claim rejection
- suggested_focus quality validation
- mocked tests only

Excluded:

- Provider v1
- full report integration
- Streamlit changes
- report persistence changes
- workout generation changes
- CrewAI changes
- parser or validator loosening
- live Ollama calls in pytest

## Model-facing payload additions
The quote-only payload now includes:

- `approved_coaching_frames`

These are backend-authored language frames. They are not raw facts and they do not authorize new factual claims. They give the model safer coach-like ways to connect approved anchors and approved interpretation claims.

Examples:

- The clearest training signals are the logged lifts with concrete load and rep detail.
- Use these logged lifts as reference points before increasing intensity.
- Keep the next session measured and continue logging load, reps, and RIR.
- Avoid chasing more intensity immediately; use the logged lifts as checkpoints first.

## Validation added
v4.3 rejects debug/internal/product-weak language such as:

- execution data
- data for review
- details are provided
- exact logged training details
- exact training details
- provided details
- allowed names
- allowed numbers
- payload
- contract
- validator
- debug
- this section
- this report section
- schema
- provider-approved
- cautious review
- should be interpreted from
- discussed without additional

v4.3 also strengthens form/control claim rejection. The following now fail unless explicitly approved:

- controlled execution
- controlled reps
- controlled movement
- technical control
- strong form
- good form
- solid form
- clean form
- movement quality
- execution quality
- clean execution
- solid execution

## Suggested focus standard
`suggested_focus` must remain practical and user-facing. It should not tell the user to review data or interpret details.

Bad:

- Review the execution data.
- Interpret the details cautiously.
- Use the exact details for guidance.

Better:

- Use Dumbbell Bench Press as a reference point and keep the next session measured.
- Keep the next session measured and continue logging load, reps, and RIR.
- Avoid chasing more intensity immediately; use the logged lifts as checkpoints first.

## Safety position
v4.3 does not make exact anchors sufficient by themselves. A candidate still must pass:

- schema validation
- exact anchor placement validation
- approved name validation
- number validation
- unsupported claim validation
- meta-copy validation
- copy-quality validation

Invalid output still falls back deterministically.
