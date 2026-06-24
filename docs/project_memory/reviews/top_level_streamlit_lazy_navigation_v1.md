# Review - Top-Level Streamlit Lazy Navigation v1

## Review status

Ready for Architecture/QA review after local and Linux validation.

## Summary

This milestone addresses the real Linux latency source identified after the Weekly Coach Summary QA Date Range Debug v2 attempt was reverted. The Developer section itself was fast, but Streamlit's eager top-level tab execution rendered Workout and History before Developer.

The implementation changes the top-level navigation from eager `st.tabs` to selected-page radio navigation. Only the selected page body is executed during a rerun.

## Boundaries confirmed

- Developer section internals are not expanded.
- Weekly QA Date Range Debug v2 is paused and not included.
- Provider runtime is unchanged.
- Deterministic behavior remains the default.
- No Ollama/CrewAI/qwen calls are added.
- No public/raw debug leakage is added.

## Required validation

- `pytest tests/test_streamlit_top_level_lazy_navigation.py -q`
- `pytest tests/test_streamlit_developer_mode_latency.py -q`
- `python -m py_compile ui/streamlit_app.py`
- Linux runtime smoke confirming Developer no longer waits for Workout/History cold renders.
