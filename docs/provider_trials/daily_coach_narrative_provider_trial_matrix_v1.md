# Daily Coach Narrative Provider Trial Matrix v1

This directory is the recommended output location for Daily Coach Narrative Provider Trial Matrix v1.

The trial matrix compares the accepted Daily Coach value-aware narrative path across:

- deterministic;
- direct_ollama;
- openai.

## Usage

Deterministic-only trial:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers deterministic \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1
```

Dry run with live providers skipped:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 101 102 103 104 105 \
  --date 2026-06-27 \
  --providers deterministic direct_ollama openai \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1
```

Live-provider trial requires explicit opt-in:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 101 102 103 104 105 \
  --date 2026-06-27 \
  --providers deterministic direct_ollama openai \
  --models direct_ollama=ollama/qwen2.5:3b openai=gpt-4.1-mini \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1 \
  --allow-live-providers
```


## Diagnostics v1 additions

Daily Coach Provider Trial Diagnostics v1 adds local-only diagnostics for provider-runtime investigation.

Diagnostic mode is explicit and off by default. Normal trial artifacts remain sanitized and must not contain raw provider text or secrets.

Local raw provider text capture:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers openai \
  --models openai=gpt-4.1-mini \
  --output-dir /tmp/daily_coach_trials \
  --allow-live-providers \
  --diagnostic-raw-output \
  --raw-output-dir /tmp/fitness_ai_provider_diagnostics
```

Ollama cleanup after live trial rows:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers direct_ollama \
  --models direct_ollama=ollama/qwen2.5:3b \
  --output-dir /tmp/daily_coach_trials \
  --allow-live-providers \
  --ollama-unload-after-run \
  --ollama-keep-alive 0
```

Safe diagnostic metadata may include provider error type, safe provider config status, live-provider allowance, diagnostic-mode status, and Ollama cleanup status. API keys, authorization headers, and raw provider text must not be written to normal JSONL/Markdown artifacts.

## Generated files

The tool writes:

- `trial_matrix.jsonl`
- `trial_matrix_summary.md`
- `selected_outputs.md`

Generated outputs should not include raw provider output or secrets. Review generated files before committing any trial artifacts.

## Product boundary

This is evaluation tooling only.

No provider becomes default through this milestone.

Deterministic remains the product default.

## Copy Grounding & Context Enrichment v1 additions

Provider trial rows now include diagnostic review fields for context-specific copy quality:

- `high_value_claims_available`
- `high_value_claims_used`
- `preferred_claims_by_field_used`
- `declared_claim_count`
- `generic_copy_flags`
- `unsupported_claim_flags`
- `section_role_flags`
- manual copy quality, specificity, coaching usefulness, and fact-dump score placeholders

These fields are review aids for Architecture/Product/Agent Engineering. They do not weaken parser, quote/value validation, deterministic fallback, or artifact safety. Raw provider output remains local-only and explicit diagnostic mode only.
