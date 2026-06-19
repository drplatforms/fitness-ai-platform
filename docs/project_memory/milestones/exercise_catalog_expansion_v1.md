# Exercise Catalog Expansion v1

Status: IMPLEMENTED / PENDING QA

Implementation status: `EXERCISE_CATALOG_EXPANSION_V1_IMPLEMENTED_PENDING_QA`

## Context

Food Catalog Expansion v1 was accepted and merged to main. The next premium-product usability gap is training variety and exercise matching.

Daily Next Action Panel v1 can route the user toward workout review, but workout preview becomes more useful when the exercise catalog has stronger coverage across the user's actual home-gym equipment, movement patterns, substitutions, recovery-friendly options, and conditioning/mobility choices.

## Goal

Expand the curated exercise catalog in a deterministic, inspectable way so workout generation and workout preview feel more varied, equipment-aware, and useful for real training.

This is product usability work. It is not AI/provider work.

## Implementation summary

The curated local exercise catalog expands from 178 to 240 entries.

Added coverage includes:

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

Representative new entries:

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

## Inventory after expansion

Current exercise catalog count: 240 entries.

Exercise types:

- strength: 173
- core: 28
- conditioning: 26
- mobility: 13

Top equipment coverage:

- dumbbell: 57
- bodyweight: 46
- plates: 43
- cable: 33
- adjustable_bench: 32
- barbell: 30
- resistance_band: 29

## Tests added or updated

Tests prove:

- expanded catalog count is expected
- new curated entries are present
- no duplicate exercise names exist
- required fields/tags are valid
- movement patterns, exercise types, difficulty values, and equipment tags are within approved sets
- mobility/recovery depth is improved
- home-gym filtering includes expanded options
- limited-equipment filtering excludes unavailable equipment
- existing workout preview compatibility remains intact

## Boundaries preserved

This milestone does not:

- change workout generation behavior
- change Training Level 5 semantics
- change Nutrition Level 5 semantics
- change provider semantics
- make direct_ollama default
- run or promote qwen3
- loosen validators
- remove deterministic fallback
- remove provider gates
- add food catalog changes
- add meal planning
- change nutrition formulas
- redesign Streamlit
- add RAG, embeddings, scraping, or agent orchestration
- add AI-generated production exercise entries
- add clinical rehab claims

## Expected QA status

`EXERCISE_CATALOG_EXPANSION_V1_ACCEPTED`
