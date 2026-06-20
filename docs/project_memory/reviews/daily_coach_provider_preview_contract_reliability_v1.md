# Daily Coach Provider Preview Contract Reliability v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW.

Summary:

Daily Coach provider preview contract reliability was improved on top of accepted main after Developer Preview Stabilization v1. The manual preview lane can now normalize common local-model response wrappers before strict parser/validator approval, while rejected/raw provider output remains excluded from normal UI.

Validation focus:

- valid clean JSON can approve
- markdown-fenced JSON can approve when otherwise valid
- qwen thinking wrappers can approve when otherwise valid
- single embedded JSON can approve when otherwise valid
- ambiguous multi-object output fails safely
- validation failures return sanitized diagnostics without rejected text
- normal Today UI still has no same-session approval controls

Manual QA required:

- run qwen2.5:3b preview for QA 102
- confirm parse_success true, validation_success true, and approved_narrative_returned true when the local model follows the contract
- confirm qwen3 probe failures fail safely with sanitized diagnostics
- confirm normal Today load does not call provider
