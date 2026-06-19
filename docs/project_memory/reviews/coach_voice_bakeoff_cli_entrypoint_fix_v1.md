# Coach Voice Bakeoff CLI Entrypoint Fix v1 Review

Status: IMPLEMENTED / READY FOR QA REVIEW

## Summary

The bakeoff harness previously required manual `PYTHONPATH` setup when running the direct CLI command from the repository root in some environments.

This patch makes the direct tool command stable by adding a local repo-root bootstrap inside `tools/coach_voice_bakeoff.py`.

## Validated behavior

The direct entrypoint should now work from the repo root:

```powershell
python tools/coach_voice_bakeoff.py --model qwen2.5:3b
```

Regression coverage verifies that:

```powershell
python tools/coach_voice_bakeoff.py --help
```

runs successfully from the repo root without `PYTHONPATH`.

## Safety position

This is a CLI/tooling fix only. It does not alter model prompts, model candidates, validation rules, output schema, production provider behavior, Streamlit, Today, reports, or model approval status.
