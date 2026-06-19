# Coach Voice Bakeoff CLI Entrypoint Fix v1

Status: IMPLEMENTED / READY FOR QA

## Purpose

Make `tools/coach_voice_bakeoff.py` runnable from the repository root without requiring manual `PYTHONPATH` setup.

Preferred direct command:

```powershell
python tools/coach_voice_bakeoff.py --model qwen2.5:3b
```

## Scope

Implemented a safe repo-root import path bootstrap inside the CLI tool before importing project services.

Added regression coverage proving the direct entrypoint can run `--help` from the repo root when `PYTHONPATH` is absent.

## Non-goals preserved

This patch does not:

- change prompts
- loosen validators
- promote any model
- approve qwen3
- change provider gates
- integrate coach voice output into Today
- integrate coach voice output into reports
- touch Streamlit
- change production provider behavior

## Expected status after QA

COACH_VOICE_BAKEOFF_CLI_ENTRYPOINT_FIX_V1_ACCEPTED
