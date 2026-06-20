# Daily Coach Provider Preview Contract Reliability v1

Status: IMPLEMENTED / READY FOR REVIEW.

This milestone keeps Daily Coach provider preview manual and Developer Mode-only while making the preview contract easier to inspect and more reliable with local Ollama/qwen output shapes.

Implemented:

- deterministic preview-output normalization before strict parsing
- safe stripping of common qwen `<think>...</think>` wrappers
- safe stripping of whole-response markdown JSON fences
- safe extraction of a single embedded JSON object from model framing
- safe rejection of ambiguous multi-object output
- stable `approved_narrative_returned` preview field
- sanitized parse/validation diagnostics surfaced in the debug response
- contract reliability tests for valid, fenced, thinking-wrapped, prose-wrapped, ambiguous, and validation-rejected provider output

Boundaries preserved:

- no same-session approval
- no `Approve for this session` UI
- no provider narrative display in normal Today UI
- no provider call on normal Today load
- no provider/model promotion
- no persistence/schema/report/workout/nutrition/catalog changes
