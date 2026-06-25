# Daily Narrative Coaching Intelligence + Voice Lab v1

Status: implemented for Architecture review

Branch: `feature/daily-narrative-coaching-intelligence-voice-lab-v1`

## Summary

Added a Developer Mode-only Daily Narrative Voice Lab for testing coaching copy across synthetic safe scenarios and real seeded QA contexts. The lab creates a repeatable workflow for generating, comparing, and critiquing deterministic Daily Narrative candidates without model promotion, automatic provider calls, or public Today behavior changes.

## Implemented

- `services/daily_narrative_voice_lab_service.py`
- `tools/dev_daily_narrative_voice_lab.py`
- Developer Mode Voice Lab panel in `ui/streamlit_app.py`
- app-side voice examples document
- updated voice contract using user feedback
- adaptive deterministic copy families for no-data, low-data, nutrition-only, training-without-fueling, rich-day, mixed-signal, workout-detail-missing, reset, and recovery-caution cases
- copy quality checks for banned and awkward phrases
- tests for fixture coverage, copy differentiation, prompt guidance, and Developer Mode boundary

## Boundaries preserved

- No public/default provider display
- No automatic generation
- No worker, queue, scheduler, polling, or background process
- No CrewAI reintroduction
- No model promotion
- No raw row/log/note/set exposure
- No workout-selection behavior changes beyond regression coverage
