# Open questions

- After Weekly Coach Summary Provider Runtime Design v1 acceptance, should the
  next milestone be Weekly Coach Summary Provider Runtime Prototype v1 -
  Developer Mode Only?
- Should the first prototype use `FITNESS_AI_OLLAMA_KEEP_ALIVE=0` for every
  qwen2.5:3b call, or should repeated manual Developer Mode preview actions use
  a short keep_alive such as `30s` or `1m`?
- Should raw provider output remain completely hidden, or should a later
  Architecture-approved Developer Mode raw/debug gate show it only ephemerally?
- Should provider candidate validation start with strict keyword/field checks or
  a richer claim-to-fact validator in the first prototype?
- Should Streamlit Theme Cleanup v1 or Workout Exercise Variety Rotation v1 be
  prioritized before provider prototype work if those trust issues become more
  disruptive?
