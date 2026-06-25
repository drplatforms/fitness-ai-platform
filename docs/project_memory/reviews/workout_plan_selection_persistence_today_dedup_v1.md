# Review — Workout Plan Selection Persistence + Today Workout De-dup v1

Implemented:
- stable Streamlit workout preview cache until explicit refresh
- select-preview endpoint that persists the exact visible approved workout plan
- Active Workout state can load the selected plan immediately after selection
- compact Today workout panel with route-to-Workout behavior
- tests for selection persistence and Today de-duplication

Follow-up still deferred:
- exercise variety / anti-repeat tuning
- broader workout generation redesign
- provider/AI workout generation
