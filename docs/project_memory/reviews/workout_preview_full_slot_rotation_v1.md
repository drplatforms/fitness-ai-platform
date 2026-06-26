# Workout Preview Full-Slot Rotation v1 Review Notes

Status: PENDING ARCHITECTURE REVIEW

Implementation target:

- Refreshed previews attempt to rotate every overlapping exercise slot when valid alternatives exist.
- Repeats are allowed only when the slot lacks safe same-pattern/equipment alternatives.
- Quick / Standard / Full sizing remains in the accepted 3-4 / 4-5 / 6-7 ranges.
- Selected and Active Workout state remains persisted and isolated from preview variation.
- Today de-dup remains preserved.
- No provider/AI workout path is introduced.

Validation expected:

- workout plan service regression tests
- workout selection/persistence regression tests
- Streamlit workout selection regression tests
- Today workout de-dup regression tests
- workout daily state lifecycle regression tests
- exercise catalog tests
- workout exercise count preference tests
- workout generation sizing/persistence stabilization tests
- new full-slot rotation tests
