# Open Questions

## Exercise Eligibility Matrix v1 follow-up

Exercise Eligibility Matrix v1 created an explicit generator-facing eligibility service and developer diagnostic, but it intentionally did not force full catalog reachability.

Current known findings from the diagnostic baseline:

- 240 active catalog exercises.
- 237 equipment-compatible exercises.
- 232 generator-eligible exercises.
- 54 exercises appeared in the 10-variation deterministic sweep.
- 186 generator-eligible exercises did not appear in that sweep.
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170).
- weak movement families: arms_biceps, arms_triceps, mobility.

Open follow-up questions:

- Should arms work remain mostly deferred, or should a future accessory slot make limited biceps/triceps work reachable?
- Should mobility exercises stay excluded until warmup/mobility slots exist?
- Should catalog reachability be improved through candidate-pool scoring, slot expansion, or a separate reachability audit first?
- Should the diagnostic eventually consume the eligibility service directly? An optional refactor patch failed to apply during v1 and was deliberately deferred instead of stacked blindly.

## Rolling multi-refresh novelty

Workout Preview Full-Slot Rotation v1 accepted immediate previous-preview anti-repeat only.

Rolling multi-refresh novelty is deferred to Workout Preview Rolling Exposure Rotation v2.

Open question: should long-window exercise exposure tracking be session-only, persisted, or derived from selected workout history?

## Full exercise eligibility and catalog reachability

Exercise Catalog Utilization / Specialized Movement Coverage v1 improved deterministic catalog breadth and specialized movement reachability.

Exercise Eligibility Matrix v1 makes eligibility explicit but does not complete all reachability work.

Future work remains:

- Catalog Reachability Audit v2.
- complete catalog reachability.
- deeper movement-family de-duplication.
- clearer equipment/movement-pattern compatibility rules.
- decision on whether candidate-only exercises should be promoted by scoring, rotation, or new slots.

## Provider strategy roadmap

Provider strategy remains pending.

Possible future planning should compare local-first `qwen` / `direct_ollama` paths with higher-tier OpenAI/provider adapter options, but no provider strategy implementation is authorized by the current exercise eligibility milestone.

Provider may propose. Backend validates. User sees only approved output.

## Complex milestone process tuning

The current process doctrine is now: bite by bite, just bigger bites.

Open questions for future process/tooling work:

- Should dev assistant generate complexity scores for proposed milestones?
- Should dev assistant generate expected file-change budgets automatically?
- Should stop-condition handoffs get a repo-owned template?
- Should feature branch validation check whether the original smoke failure has a corresponding regression or diagnostic test?

## Daily Narrative feedback hardening

The first feedback-driven deterministic copy hardening pass is implemented. A future milestone may decide whether to continue provider-facing examples and validation prompt guidance, or pause Daily Narrative while workout/catalog/nutrition systems continue maturing.

## Feedback storage lifecycle

The v1 feedback store is local JSONL and should not be committed by default. A future milestone may decide whether selected approved examples should be manually promoted from runtime feedback into project-memory docs. Raw runtime JSONL should not be committed.

## Model selection

Do not treat bad copy or strict-schema failures as a model-size issue by default. The current priority is better approved context, stricter contracts, deterministic fallback, diagnostics, and well-scoped provider experiments.
