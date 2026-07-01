# Recovery Intelligence v2 Architecture Plan

**Status:** Architecture plan / implementation scope guard
**Baseline:** `fc7ed70 main_merge-post-north-star-state-reconciliation-v1`
**Source snapshot:** `fitness_ai_snapshot_2026-06-30_fc7ed70_main_merge-post-north-star-state-reconciliation-v1.zip`
**Owner:** Architecture
**Next implementation milestone after acceptance:** `Recovery Intelligence v2 Model Contract v1`

This document defines how Recovery Intelligence should evolve after v1. It is a planning artifact, not an implementation patch.

No Python, API, Streamlit, provider, persistence, report, recommendation, RAG, vector, agent, or SaaS work is authorized by this document alone.

## Current v1 Ground Truth

Recovery Intelligence v1 already provides a real deterministic source-data layer:

- reads from `daily_checkins`
- uses `checkin_date` as the primary date
- uses `created_at` / `id` only for duplicate same-day resolution
- deduplicates same-day check-ins
- builds 7, 14, and 28 day recovery windows
- builds recent 7-day vs prior 7-day trend comparison
- classifies sleep, energy, soreness, readiness, fatigue risk, and confidence
- emits reason codes, limitations, source facts, and a coach-safe summary
- blocks diagnostic / medical language such as overtraining, injury, illness, sleep disorder, diagnosis, and medical risk

Recovery v2 should extend this pattern. It should not rewrite the product brain or replace existing source-data contracts casually.

## Product Goal

Recovery v2 should make backend recovery interpretation more useful to Daily Coach intelligence and future recommendation layers while keeping backend truth separate from AI explanation.

The backend should be able to safely determine statements such as:

```text
Recovery appears supportive.
Recovery may be limiting training readiness.
Recovery data is too incomplete to make a confident call.
Recovery is improving after a lower-stress period.
Sleep, energy, and soreness signals are mixed.
```

It should not diagnose, prescribe, or overclaim.

## Architecture Doctrine

Recovery v2 follows the platform north-star doctrine:

- Backend owns truth.
- Deterministic logic comes first.
- Provider output may explain approved facts later, but it never becomes recovery truth.
- Confidence, provenance, limitations, and data quality are first-class outputs.
- Source-data gaps must be visible instead of hidden.
- No medical, diagnostic, injury, illness, sleep-disorder, or overtraining claims.

## Proposed V2 Contract Shape

The implementation may choose exact class names, but the v2 model contract should represent these concepts explicitly.

```text
RecoveryIntelligenceV2Summary
- user_id
- target_date
- generated_at
- source_table
- model_version
- current_day
- windows
- baseline
- recent_vs_baseline
- recent_vs_prior
- sleep_interpretation
- energy_interpretation
- soreness_interpretation
- body_weight_interpretation
- checkin_consistency
- readiness_classification
- recovery_pressure
- fatigue_support
- data_quality
- confidence
- source_facts
- coach_safe_summary
- reason_codes
- limitations
```

Supporting contracts should be narrow and serializable:

```text
RecoveryBaseline
- baseline_window_days
- start_date
- end_date
- checkin_days
- average_sleep_hours
- average_energy_level
- average_soreness_level
- latest_body_weight_lb
- confidence
- reason_codes
- limitations
```

```text
RecoverySignalInterpretation
- signal_name
- current_value
- baseline_value
- recent_average
- prior_average
- delta_from_baseline
- delta_recent_vs_prior
- status
- trend_direction
- confidence
- reason_codes
- limitations
```

```text
RecoveryDataQuality
- expected_days
- checkin_days
- checkin_rate
- missing_sleep_days
- missing_energy_days
- missing_soreness_days
- duplicate_days_collapsed
- stale_current_day
- status
- confidence
- reason_codes
- limitations
```

## Recommended Classification Values

Use simple bounded enums first.

### Readiness Classification

```text
unknown
recovery_limited
manageable
supportive
improving
mixed
```

### Recovery Pressure

```text
unknown
low
moderate
high
```

### Signal Status

```text
unknown
low
borderline
normal
high
mixed
```

### Trend Direction

```text
unknown
improving
stable
worsening
mixed
```

### Data Quality Status

```text
missing
limited
partial
usable
strong
```

### Confidence

```text
Limited
Low
Moderate
High
```

Keep labels boring. The useful part is the evidence behind them.

## Windowing and Baseline Rules

Recovery v2 should keep the existing 7/14/28-day windows but make baseline interpretation more explicit.

Recommended v2 window stack:

```text
current_day
recent_7_days
prior_7_days
rolling_14_days
rolling_28_days
baseline_window
```

Baseline construction should prefer the best available 28-day signal. If 28-day coverage is weak, v2 may degrade to 14-day or mark baseline confidence as Limited/Low.

Minimum guidance:

- 0 check-ins: no recovery claims; data quality `missing`.
- 1-2 check-ins: current context only; no trend claims.
- 3-4 check-ins: limited trend language only.
- 5-6 check-ins in 7 days: usable recent window.
- 7+ check-ins with adequate coverage: stronger confidence possible.

Do not invent missing values. Missing fields remain unknown, not zero.

## Signal Interpretation Guidance

### Sleep

Recovery v2 may consider:

- average sleep over recent windows
- change vs prior window
- change vs baseline
- low sleep streaks
- missing sleep coverage

Allowed framing:

```text
Sleep has been lower than your recent baseline.
Sleep appears consistent enough to support training readiness.
Sleep data is incomplete, so recovery confidence is limited.
```

### Energy

Recovery v2 may consider:

- average energy
- declining energy trend
- improving energy trend
- conflict between energy and soreness/sleep

Allowed framing:

```text
Energy is trending down compared with the prior window.
Energy is improving, but soreness is still elevated.
```

### Soreness

Recovery v2 may consider:

- average soreness
- rising soreness
- high soreness streaks
- soreness improvement after deload/reduced-stress period

Allowed framing:

```text
Soreness is elevated compared with the prior window.
Soreness is trending down, which supports a controlled progression approach.
```

### Body Weight

Recovery v2 may carry body-weight deltas as context only. It should not infer fat loss, muscle gain, hydration status, medical concern, or nutrition adequacy from weight alone.

Allowed framing:

```text
Body weight changed over the window, but this is context only and should not drive recovery conclusions by itself.
```

## Readiness and Recovery Pressure Rules

Recovery pressure should be evidence-supported and cautious.

Examples:

```text
low recovery pressure:
- adequate sleep
- usable/strong energy
- low/moderate soreness
- usable data quality

moderate recovery pressure:
- one clear limiting signal
- multiple borderline signals
- mixed signals with usable data

high recovery pressure:
- multiple limiting signals with usable data
- low sleep plus low energy
- high soreness plus declining energy
```

If data quality is Limited, readiness should usually be `unknown` or `mixed`, and recovery pressure should avoid strong claims.

## Interaction With Workout Set Intelligence

Recovery v2 should not make training changes by itself.

Workout Set Intelligence provides training effort/load context. Recovery v2 provides recovery-source context. Daily Coach Intelligence Snapshot and future recommendation policy layers may combine both.

Allowed future pattern:

```text
Recovery v2: sleep is lower and soreness is elevated.
Workout Set Intelligence: recent working sets were close to failure.
Recommendation layer: keep most sets around RIR 2-3 today.
```

Forbidden pattern:

```text
Recovery v2 alone says the user must deload.
```

## Daily Coach Intelligence Snapshot Integration

After v2 models and service are accepted, a later integration milestone may update the snapshot layer.

Future snapshot status should become:

```text
recovery_intelligence: implemented_v2
```

But this planning milestone does not change snapshot runtime behavior.

## Allowed Coaching Language

Allowed user-facing language must stay cautious and source-backed:

```text
Recovery may be limiting readiness today.
Sleep has been lower than your recent baseline.
Soreness is elevated compared with the prior window.
Energy is trending down.
Recovery data is limited because check-ins are incomplete.
Recovery appears supportive enough for controlled progression.
Signals are mixed, so use a conservative training approach.
```

## Forbidden Coaching Language

Recovery v2 must not produce or authorize:

```text
overtraining
injury
illness
diagnosis
sleep disorder
medical risk
you must deload
you are not recovering
you failed recovery
this caused stalled progress
this caused fat gain or fat loss
this proves nutrition is inadequate
```

The existing forbidden-language guard should remain and may be expanded in implementation.

## Recommended Implementation Sequence

### 1. Recovery Intelligence v2 Model Contract v1

Owner: Backend Development.

Scope:

- add v2 model contracts
- add enum validation
- add serialization tests
- no service behavior changes yet
- no snapshot integration yet
- no Daily Coach behavior changes

Likely files:

```text
models/recovery_intelligence_v2_models.py
tests/test_recovery_intelligence_v2_models.py
```

### 2. Recovery Intelligence v2 Service v1

Owner: Backend Development.

Scope:

- deterministic read-only v2 service
- builds v2 summary from daily_checkins
- uses explicit baseline / data quality / signal interpretation logic
- no provider calls
- no persistence mutation
- no UI/API behavior changes unless scoped

Likely files:

```text
services/recovery_intelligence_v2_service.py
tests/test_recovery_intelligence_v2_service.py
```

### 3. Daily Coach Intelligence Snapshot Recovery v2 Integration

Owner: Backend Development, with Architecture acceptance.

Scope:

- swap/add v2 recovery intelligence in snapshot contract
- preserve v1 compatibility only if needed
- update developer artifact tool
- update source-data gaps / completeness
- no user-facing copy changes

### 4. Recommendation / Daily Coach Usage

Only after source-data behavior is tested and accepted.

Scope should be separately planned before Recovery v2 influences ApprovedActionPlan, workout guidance, nutrition guidance, reports, or provider context.

## Test Expectations

Model-contract tests should cover:

- valid summary construction
- invalid enum rejection
- Limited/Low confidence requiring reason_codes or limitations
- missing data quality fields handled explicitly
- safe serialization to dict
- forbidden text rejected where model owns user-facing summaries

Service tests should eventually cover:

- no check-ins
- one check-in
- limited check-in coverage
- strong 7-day coverage
- recent low sleep
- improving sleep after prior poor window
- rising soreness
- declining energy
- mixed signals
- duplicate same-day check-ins
- missing sleep/energy/soreness fields
- body-weight context present but non-authoritative
- forbidden language guard

Snapshot integration tests should eventually cover:

- recovery v2 appears in source services/status
- data completeness reflects v2 fields
- source_data_gaps remain honest
- existing Workout Set Intelligence remains intact
- normal Today behavior remains unchanged unless separately scoped

## Non-Goals

This architecture plan does not authorize:

- Python implementation inside this docs-only milestone
- API changes
- Streamlit changes
- database schema changes
- provider prompt changes
- OpenAI/Ollama/CrewAI changes
- recommendation behavior changes
- automatic deloads
- workout plan changes
- nutrition target changes
- report copy changes
- RAG/vector/embedding work
- wearable/HRV integration
- medical claims

## Acceptance Criteria For This Plan

This plan is acceptable when:

- the v2 scope is narrow enough for Backend to implement in staged slices
- backend-owned facts/confidence/provenance/limitations remain explicit
- provider output remains out of scope
- Daily Coach Snapshot integration is sequenced after model/service acceptance
- recommendation behavior changes are deferred until source-data behavior is proven
- Linux/Windows workflow rules remain preserved in project memory
