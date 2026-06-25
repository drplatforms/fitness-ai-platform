# Workout Plan Selection Persistence + Today Workout De-dup v1

Status: implemented / ready for Architecture review.

This milestone fixes the Workout preview -> Select This Workout -> Active Workout persistence and removes the duplicate full workout selection flow from Today. The Workout page remains the canonical Plan / Active / Review surface. Today now provides only compact workout status and route-to-Workout behavior.

Boundaries preserved:
- no provider or AI workout generation changes
- no exercise variety / rotation work
- no Streamlit theme cleanup
- no automatic generation, worker, queue, scheduler, or polling
- no CrewAI / Ollama changes
