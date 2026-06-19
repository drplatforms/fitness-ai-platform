# Daily Coach Narrative Provider Contract Tightening v1.1 Runtime QA

Status: `DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_IMPLEMENTED_PENDING_RUNTIME_QA`

## Purpose

This runtime QA verifies that the tightened Daily Coach Narrative validator rejects meta/process/internal architecture language while preserving safe, grounded, coach-like output.

## Required model matrix

Required:

- `qwen3:8b` x users 101, 102, 105
- `qwen2.5:3b` x users 101, 102, 105

Optional:

- `qwen3:32b` x users 101, 102, 105

## Required command

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

Inspect:

```powershell
Get-Content .\artifacts\daily_coach_narrative_offline_qa_v1\report.md | Select-Object -First 320
```

Optional reference:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:32b --user-id 101 --user-id 102 --user-id 105
```

## Acceptance checks

PASS if:

- validator rejects explicit meta/process/internal architecture language
- qwen2.5-style meta phrases are rejected or no longer produced
- qwen3:8b remains approved for users 101, 102, 105
- normal coach-like copy still passes
- exact recommended focus validation remains strict
- exact approved fact validation remains strict
- forbidden claim validation remains strict
- changed action/workflow target validation remains strict
- invented food/exercise/number/target validation remains strict
- deterministic fallback remains available
- no production integration occurs
- no model is promoted

PARTIAL PASS if:

- validator correctly rejects meta/process language
- qwen3:8b has one contained failure
- qwen2.5:3b becomes mostly rejected due to copy quality
- failures are safely contained
- no production integration occurs

FAIL if:

- meta/process language still passes
- validators are loosened
- qwen3:8b safe copy is broadly rejected without reason
- model output bypasses validation
- unsupported facts are accepted
- rejected output leaks
- normal UI/report integration appears
- qwen3 is promoted
- direct_ollama default changes

## Runtime result placeholder

Runtime QA has not been run in the implementation sandbox because live Ollama is local-only.

Paste the local runtime matrix here during QA review.

## First Runtime QA Result

Status: `PARTIAL_PASS_NOT_READY_FOR_MERGE`

Result summary:

- `qwen3:8b`: parse success 3/3, approved 0/3 after first v1.1 tightening
- `qwen2.5:3b`: parse success 3/3, approved 1/3 after first v1.1 tightening

Interpretation:

- Safety gate worked: meta/internal language and changed-action output were rejected.
- Product copy failed: provider prompt/context still caused too much internal phrasing.
- The branch was not ready for merge after the first runtime QA pass.

## Runtime Fix QA Plan

Rerun:

```powershell
python tools\daily_coach_narrative_offline_qa.py --model qwen3:8b --model qwen2.5:3b --user-id 101 --user-id 102 --user-id 105
```

PASS requires:

- qwen3:8b mostly or fully recovers to approved coach-like copy
- no meta/internal language appears in coach-facing fields
- exact fact validation remains strict
- changed action/workflow target validation remains strict
- failed qwen2.5 output remains safely rejected if copy quality is not acceptable
- no product integration occurs

## Final runtime QA result

Status: DAILY_COACH_NARRATIVE_PROVIDER_CONTRACT_TIGHTENING_V1_1_ACCEPTED_PENDING_ARCHITECTURE_REVIEW

Runtime QA rerun after citation/action focus fix produced a clean matrix pass.

Required users:
- 101
- 102
- 105

Models tested:
- qwen3:8b
- qwen2.5:3b
- qwen3:32b

Result summary:
- qwen3:8b: parse 3/3, validation 3/3, decision 3/3, grounding 5, voice 4, latency roughly 31-55s
- qwen2.5:3b: parse 3/3, validation 3/3, decision 3/3, grounding 5, voice 4, latency roughly 20-25s
- qwen3:32b: parse 3/3, validation 3/3, decision 3/3, grounding 5, voice 4, latency roughly 132-254s

Accepted interpretation:
- qwen3:8b remains the best practical Daily Coach Narrative evaluation candidate.
- qwen2.5:3b is a safe small-model baseline but has plainer copy.
- qwen3:32b remains useful as an offline quality reference but is too slow for practical preview loops.
- No model is production-approved.
- No Developer Preview or normal UI integration is approved by this milestone.

Representative safe excerpts:
- qwen3:8b / user 101: Focus on low-risk training to match today's recovery needs.
- qwen3:8b / user 102: Log a meal or snack to improve today's nutrition picture.
- qwen3:8b / user 105: Log a meal or snack to improve today's nutrition picture.
- qwen2.5:3b / user 101: Today, focus on keeping today's training lower-risk and controlled due to current recovery state.
- qwen2.5:3b / user 102: Today's nutrition state is limited until more food data is logged.
- qwen2.5:3b / user 105: Today's nutrition state is limited until more food data is logged.
- qwen3:32b / user 101: Keep training conservative to align with today's recovery state.
- qwen3:32b / user 102: Log a meal or snack to improve today's nutrition picture.
- qwen3:32b / user 105: Log a meal or snack to improve today's nutrition picture.

Boundary confirmation:
- no normal Today UI integration
- no Streamlit normal surface integration
- no report integration
- no persistence of model-generated narrative
- no model promotion
- qwen3 remains not production-approved
- direct_ollama remains opt-in only
- deterministic fallback remains available
- validators remain strict
