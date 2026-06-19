# Exercise Catalog Audit v1

Last updated: 2026-06-18

## Status

`EXERCISE_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`

This audit documents the current exercise catalog after Exercise Catalog Expansion v1. The implementation expands curated seed data only. It does not change workout generation logic, Training provider semantics, Nutrition provider semantics, Daily Next Action priority order, Streamlit UI, or report/persistence boundaries.

## Current inventory after Exercise Catalog Expansion v1

The app has a curated local exercise catalog seeded through `services/exercise_catalog_service.py` and `scripts/seed_exercise_catalog.py`.

Current curated catalog count observed in the implementation snapshot:

- exercise catalog entries: 240
- prior planning inventory: 178
- curated entries added in Exercise Catalog Expansion v1: 62

Current exercise types:

- strength: 173
- core: 28
- conditioning: 26
- mobility: 13

Current movement-pattern coverage:

- horizontal_pull: 31
- horizontal_push: 27
- hinge: 23
- conditioning: 21
- vertical_push: 19
- lunge: 18
- arms_biceps: 18
- squat: 16
- core_anti_extension: 16
- vertical_pull: 15
- arms_triceps: 13
- core_anti_rotation: 11
- carry: 7
- mobility: 5

Current equipment coverage:

- dumbbell: 57
- bodyweight: 46
- plates: 43
- cable: 33
- adjustable_bench: 32
- barbell: 30
- resistance_band: 29
- rack: 14
- pull_up_bar: 13
- ez_bar: 10
- treadmill: 8
- bike: 7
- rope_cable_attachment: 7
- exercise_ball: 6
- machine: 3

Current difficulty coverage:

- beginner: 134
- intermediate: 94
- advanced: 12

Current app-facing model fields remain:

- `name`
- `exercise_type`
- `movement_pattern`
- `primary_muscle_groups`
- `equipment_required`
- `difficulty`

## Expansion summary

Exercise Catalog Expansion v1 adds curated, reviewable entries across:

- bodyweight scaling options
- low-stress core options
- mobility/recovery drills
- dumbbell pressing, rowing, lower-body, arm, carry, and hinge variants
- barbell/rack/plate options
- EZ bar accessory options
- pull-up bar hold/progression options
- resistance band push, pull, hinge, squat, anti-rotation, and mobility options
- cable push, pull, hinge, anti-rotation, and accessory options
- treadmill and bike lower-intensity conditioning options

Representative new entries include:

- Wall Push-Up
- Scapular Push-Up
- Plank Shoulder Tap
- Reverse Crunch
- Cat-Cow
- Quadruped T-Spine Rotation
- Half-Kneeling Hip Flexor Stretch
- Dumbbell Squeeze Press
- Dumbbell Suitcase Deadlift
- Dumbbell Farmer March
- Rack Pull
- Barbell Shrug
- Band Chest Press
- Band Romanian Deadlift
- Cable Chest Press
- Cable Romanian Deadlift
- Treadmill Recovery Walk
- Bike Easy Spin

## Current strengths

- The catalog remains curated and deterministic.
- Home-gym equipment coverage is stronger across dumbbells, bench, barbell/rack/plates, cables, bands, pull-up bar, treadmill, and bike.
- Movement-pattern coverage is broad enough for workout preview variety and future substitution work.
- Mobility/recovery depth is improved without adding clinical rehab claims.
- Limited-equipment filtering still excludes bench, cable, barbell, rack, plates, rope, exercise ball, treadmill, bike, and machine options when unavailable.
- Machine exercises remain limited and excludable for home-gym users.

## Remaining gaps

Exercise Catalog Expansion v1 deliberately does not add schema fields for:

- secondary muscles
- substitution group
- joint stress
- recovery suitability
- progression type
- setup notes
- safety notes

Those remain candidate v2/schema-review fields.

The catalog still relies on inferred substitution behavior from existing fields:

- movement pattern
- equipment required
- primary muscle groups
- difficulty

## Curation rules preserved

An exercise qualifies as catalog-ready only when:

- display name is clear and non-duplicative
- movement pattern is explicit
- required equipment is accurate
- primary muscles are listed conservatively
- difficulty is reasonable
- high-skill or high-load options are not expected to be surfaced aggressively during recovery-limited plans
- the entry fits existing deterministic seed/test behavior

Duplicates are avoided by normalized name review.

Equipment tags are limited to existing supported equipment names, including the user's home gym equipment.

## Non-goals preserved

This milestone does not add:

- generated exercise dumps
- scraping
- RAG or embeddings
- AI-authored production catalog entries
- new workout generation behavior
- provider/report behavior changes
- Training Level 5 semantic changes
- Nutrition Level 5 semantic changes
- progression algorithms
- clinical rehab claims
- Streamlit redesign
- food catalog changes

## Expected next status

If accepted by Architecture/QA:

`EXERCISE_CATALOG_EXPANSION_V1_ACCEPTED`

Recommended next product milestones after acceptance:

- Logging UX Speed & Friction Reduction v1
- Bounded Coach Voice Bakeoff v1
- Daily Coach Narrative v1
