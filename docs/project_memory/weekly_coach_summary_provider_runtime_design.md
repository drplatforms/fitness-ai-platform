# Weekly Coach Summary Provider Runtime Design v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW
Branch: `feature/weekly-coach-summary-provider-runtime-design-v1`
Design only: no provider runtime execution is added.

## Core rule

Backend tells the truth. Provider improves the voice. Validator decides what
survives. Deterministic fallback always works.

## Future runtime flow

```text
selected user/date range
→ backend-owned WeeklyCoachSummaryContext
→ deterministic baseline
→ qwen2.5:3b candidate wording
→ parser
→ validator
→ approved public-safe Weekly Coach Summary
→ selected-range persistence
→ Developer Mode preview first
→ public/default display later, only after separate acceptance
```

This milestone designs that path only. It does not call qwen, Ollama, CrewAI, or
any provider for Weekly Coach Summary.

## Approved future model

Future Developer Mode-only prototype model: `qwen2.5:3b`.

Not approved:

- qwen3
- qwen3:32b
- CrewAI orchestration
- automatic model selection
- public/default model execution

The accepted Provider Runtime Resource Lifecycle policy applies to all future
prototype calls. Default local provider behavior must use conservative
`keep_alive`, unload-after-request where policy requires it, named-model-only
manual unload, and deterministic fallback if lifecycle cleanup or provider access
fails.

## Provider input contract

Allowed input source: `WeeklyCoachSummaryContext` built by the backend-owned QA
date-range context service. Streamlit UI state and display labels are not valid
provider input.

Allowed fields:

- `user_id` or safe debug user label
- `scenario`
- `start_date`
- `end_date`
- `source: qa_date_range_debug`
- `confidence`
- `data_quality_label`
- `limitations`
- `reason_codes`
- `fact_counts`
- safe recovery aggregate summary
- safe nutrition aggregate summary
- safe training aggregate summary
- deterministic baseline summary
- voice/tone contract
- output schema instructions

Forbidden input:

- raw DB rows
- raw food descriptions
- raw daily check-in notes
- raw workout set rows
- raw SQL
- secrets or environment values
- prompt/debug internals not required by the provider
- hidden chain-of-thought
- scratchpad
- previous failed or rejected provider output

Provider receives only bounded backend facts and safe derived labels.

## Provider output contract

Candidate schema name: `CandidateWeeklyCoachSummaryProviderOutput`.

Required JSON fields:

- `title`
- `summary`
- `recovery_note`
- `nutrition_note`
- `training_note`
- `next_action`
- `confidence_label`
- `data_limitations`
- `facts_used`
- `safety_flags`
- `provider_model`
- `source_context_metadata`
- `generated_at`

Provider output must be JSON only. It must not include markdown wrappers,
freeform lead-in text, tables, raw context, prompts, chain-of-thought, raw rows,
unsupported claims, medical diagnosis, shame/guilt language, fake certainty, or
broad wellness fluff.

## Parser behavior

The future parser must:

- accept only a JSON object
- reject invalid JSON
- reject freeform wrappers such as "Here is the JSON"
- reject arrays and markdown blocks
- map JSON into `CandidateWeeklyCoachSummaryProviderOutput`
- preserve parser failures as safe Developer Mode status only
- never display raw provider output by default

## Validator behavior

The future validator must reject provider output if it:

- is invalid JSON or schema-invalid
- misses required fields
- exceeds length bounds
- includes raw provider/debug text
- includes prompt text, scratchpad, or chain-of-thought language
- includes unsupported claims
- includes medical diagnosis
- includes shame/guilt language
- claims facts not present in context
- overstates confidence for low-data user 105
- references raw rows or private notes
- suggests unsafe behavior
- uses generic filler or banned phrases
- fails public-safe/displayable rules
- does not include factual "because" grounding where required

The validator may accept only if the output is parseable, schema-valid, grounded
in the allowed context, respectful of data quality, public-safe, readable, and
contains one clear next action.

Fallback rule: parser or validator failure keeps the deterministic summary as
the displayed and persistence-safe output.

## Voice and tone contract

Target voice:

- warm but not cheesy
- plainspoken
- coach-like, not clinical
- specific to the facts
- grounded in "because"
- no fake hype
- no guilt or shame
- no vague wellness jargon
- no "optimize your journey" language
- no robotic phrasing
- no generic filler
- confidence matches data quality
- one clear next move
- respects limited data

Weak: "Your nutrition consistency can support better training outcomes."

Better: "You logged meals most days this week, so we have enough signal to spot
a pattern: training is easier to interpret when nutrition is not a blank spot."

Weak: "Focus on logging more data to improve future recommendations."

Better: "I do not have enough logged detail to make a strong call this week.
The useful move is simple: log one meal and one workout note so next week's
summary can be based on something real."

Daily Narrative example for downstream voice work:

"Because there are no nutrition entries for today, 2026-06-23, the most useful
move is to log one meal or snack. That gives the coach something real to work
from instead of guessing."

## Grounding requirements

Each major recommendation must trace to a context fact.

Allowed:

- "Because this week has limited workout detail, I would treat the summary as a low-confidence read."
- "You logged nutrition across seven days, so the nutrition signal is stronger than usual."
- "There are workout sessions but no actual set details in this range, so progression comments should stay conservative."

Not allowed unless supported:

- "Your training intensity improved this week."
- "Your recovery is excellent."
- "Your nutrition is optimized."

## Happy path scenario

User 102 `aligned_managed`
Range: 2026-05-31 through 2026-06-06

Known facts:

- selected recovery: 9 rows
- selected nutrition: 21 rows across 7 logged days
- selected workout sessions: 5 rows
- selected planned workouts: 1 row / 4 planned exercises
- selected actual sets: 0 rows
- data quality: usable

Future provider candidate should be useful, warm, grounded, specific to
nutrition/recovery coverage where supported, conservative on progression because
actual sets are zero, and include one clear next action.

## Low-data scenario

User 105 `data_quality_limited`
Range: 2026-05-31 through 2026-06-06

Known facts:

- selected recovery: 1 row
- selected nutrition: 5 rows across 3 logged days
- selected workout sessions: 2 rows
- selected actual sets: 0 rows

Future provider candidate must use limited/cautious tone, explicitly mention
data limitations, avoid confidence overstatement, and recommend a simple next
action.

## Out-of-range scenario

Example stale range: 2026-06-08 through 2026-06-14.

The provider should generally not be called when selected context is
insufficient. Deterministic insufficient-data fallback should usually win. If a
future prototype calls the provider anyway, validator must enforce no-data or
low-confidence behavior.

## Developer Mode provider preview design

Future Developer Mode-only preview should show:

- selected user/date range
- build context button
- deterministic baseline output
- provider lifecycle policy display
- manual provider preview button
- provider response parse status
- validator status
- approved candidate display only if valid
- deterministic fallback display if invalid

Future buttons:

1. Build selected-range context
2. Generate deterministic baseline
3. Generate provider candidate manually
4. Validate provider candidate
5. Save approved provider summary

No automatic generation on page load. No automatic provider calls when opening
Developer page. No normal UI provider call.

## Persistence boundary

Approved for future prototype:

- approved provider summary may be persisted only after parse + validation pass
- persistence must include selected user/date range
- persistence must include source/provider metadata
- persistence must not include raw prompt
- persistence must not include raw provider output unless separate safe debug storage is explicitly approved later
- rejected output must not be persisted as user-facing summary
- deterministic fallback remains safe persisted option

Suggested metadata:

- `user_id`
- `start_date`
- `end_date`
- `provider_name`
- `provider_model`
- `lifecycle_policy_used`
- `context_source`
- `validation_status`
- `generated_at`
- `approved_at`
- `public_safe`
- `displayable`

## Failure modes

Failure handling must keep deterministic output and show only safe Developer Mode
messages for:

- Ollama unreachable
- timeout
- model missing
- model unload failure
- invalid JSON
- schema validation failure
- unsupported claim detected
- low-data overconfidence
- unsafe phrase detected
- context too sparse
- provider response empty or too long
- lifecycle cleanup failure

Rejected/raw provider output is not displayed or persisted.

## CrewAI position

CrewAI remains deferred. Weekly Coach Summary provider runtime does not need
orchestration yet.

Use direct_ollama + qwen2.5:3b + strict schema + validator + fallback first.
Reconsider CrewAI only if later milestones require multi-step tool use,
planner/verifier split, critique/rewrite, multi-agent comparison, or broader
cross-domain synthesis.

## Future prototype test plan

Future tests should prove:

1. provider input builder includes only allowed context fields
2. provider input excludes raw rows, prompts, and scratchpad
3. provider output schema model validates required fields
4. parser rejects invalid JSON
5. validator rejects unsupported claims
6. validator rejects overconfident low-data output
7. validator rejects medical claims and shame/guilt language
8. validator rejects raw provider/debug leakage
9. validator accepts grounded output for user 102 happy path
10. validator accepts cautious output for user 105 low-data path
11. timeout or unreachable Ollama returns deterministic fallback
12. lifecycle keep_alive is passed into provider request
13. unload-after-request path is called when policy requires
14. rejected provider candidate is not persisted
15. approved provider candidate can be persisted under selected user/date range
16. normal/default UI does not show provider preview
17. no provider call happens on Developer page open

## Next implementation milestone

Weekly Coach Summary Provider Runtime Prototype v1 - Developer Mode Only.

The prototype may manually call qwen2.5:3b against the bounded context seam only
after this design is accepted. Public/default display, normal Today display,
automatic generation, workers, queues, schedulers, polling, CrewAI, qwen3, and
qwen3:32b remain deferred.
