# Exercise Catalog Utilization / Specialized Movement Coverage v1

Status: implemented / ready for Architecture review.

Branch: `feature/exercise-catalog-utilization-specialized-movement-coverage-v1`

Goal: improve deterministic workout candidate pool coverage so the generator can use more of the existing catalog and surface specialized movements where safe, without changing selected-workout persistence or introducing AI workout generation.

Implemented:

- catalog-backed same-pattern alternatives for workout template slots
- deterministic candidate-pool expansion that preserves slot movement-pattern intent
- equipment filtering for all catalog-backed alternatives
- avoided-movement filtering for expanded catalog options
- bounded top-candidate rotation so variation can reach more catalog entries
- data-quality-limited plans stay simple and avoid harder specialized expansion
- diagnostic catalog utilization report helper
- tests for catalog reachability, missing pattern coverage, specialized movement reachability, deterministic variation, and equipment/template safety

Preserved:

- deterministic workout generation
- selected workout immutability
- Active Workout loading behavior
- Today workout de-duplication
- explicit preview refresh semantics
- workout validation
- Daily Narrative accepted behavior
- Weekly Summary behavior

Not included:

- no AI/provider workout generation
- no CrewAI/Ollama/OpenAI/PydanticAI/LangGraph
- no worker/queue/scheduler/polling
- no full workout engine rewrite
- no selected workout mutation
- no Streamlit latency optimization
- no Daily Narrative/provider changes
- no Weekly Summary changes
