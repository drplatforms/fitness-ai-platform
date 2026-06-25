# Review Notes — Exercise Catalog Utilization / Specialized Movement Coverage v1

Status: implemented / ready for Architecture review.

The implementation broadens deterministic workout slot candidate pools by adding catalog-backed alternatives that match the existing template slot movement patterns and current equipment constraints.

Safety/order of operations:

1. template slot intent remains primary
2. movement pattern must match the slot
3. available/unavailable equipment must be respected
4. avoided movements remain excluded
5. data-quality-limited sessions remain simple
6. variety participates only after safety/template constraints pass
7. selected workouts remain immutable after selection

Validation targets:

- exercise catalog service tests
- workout plan service tests
- workout selection/persistence tests
- Streamlit workout selection tests
- Today workout de-dup tests
- workout daily state lifecycle tests
- Daily Narrative regression tests
- Weekly Summary regression tests
- project memory checks
- Linux pull/smoke
- browser smoke

Architecture review should confirm whether this is sufficient for:

`EXERCISE_CATALOG_UTILIZATION_SPECIALIZED_MOVEMENT_COVERAGE_V1_ACCEPTED`
