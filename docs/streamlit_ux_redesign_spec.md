# Streamlit UX Redesign Spec v1 — User Vision Lock

## Purpose

This document locks the target Streamlit user experience before additional UI implementation.

The current backend and workout architecture are strong, but the Streamlit app still feels too much like a backend/admin workbench. The goal of the next UI phase is to make the app feel useful for a real daily workout while preserving the existing backend behavior.

This is a design-only milestone. It does not require backend schema changes, recommendation response-shape changes, CrewAI workout generation, automatic progression, weekly periodization, or report behavior changes.

## Current UX Problem

The current app exposes too much implementation detail to the normal user.

The main pain points are:

- too much scrolling
- too many stacked sections
- too many visible technical IDs
- too much raw data
- too many disconnected workout panels
- nutrition is not prominent enough as its own workflow
- Exercise Catalog feels too dominant as a top-level tab
- planned-vs-actual review is too verbose and text-heavy
- substitution behavior exists but is not integrated cleanly into the workout flow
- the normal user path is not obvious enough:
  - what workout should I do?
  - why this workout?
  - how do I start?
  - how do I log sets?
  - how do I complete?
  - what happened afterward?

## UX North Star

The app should feel like a daily fitness coach, not a backend console.

When the user opens the app, they should quickly understand:

1. what the app recommends today
2. whether recovery/nutrition data is missing
3. what workout to do
4. how to start the workout
5. how to log actual work
6. how to complete the workout
7. what changed compared with the plan

Technical detail should still be available, but only in Developer Mode.

## Top-Level Navigation

Keep top tabs, but reorganize them.

Recommended top-level tabs:

1. Today
2. Workout
3. Nutrition
4. History
5. Reports
6. Developer

### Navigation Rules

- Today is the default landing page.
- Workout owns the full workout workflow.
- Nutrition is its own top-level tab and should not be nested under Log Workout.
- Exercise Catalog should not be a top-level tab for now. It should live inside Workout.
- Developer contains raw payloads, IDs, debug fields, runtime metadata, and internal responses.
- Normal user mode should avoid plan IDs, execution IDs, raw JSON, internal reason codes, and backend debug payloads.

## Global Layout Principles

### Normal Mode

Normal mode should prioritize:

- recommendations
- action prompts
- workout cards
- simple forms
- concise summaries
- visual planned-vs-actual feedback

Normal mode should hide:

- raw API responses
- plan instance IDs
- execution session IDs
- workout session IDs
- internal enum values where a friendly label exists
- backend reason codes
- validation/debug metadata
- raw JSON

### Developer Mode

Developer Mode should be a sidebar toggle.

When enabled, it may expose:

- plan IDs
- execution session IDs
- workout session IDs
- raw backend responses
- API payloads
- runtime metadata
- debug fields
- internal reason codes
- raw planned-vs-actual summary JSON
- raw recommendation JSON
- raw report/job metadata

Developer Mode should still be organized with expanders and should not overwhelm the main workflow.

## Today Tab

Today should be the default landing page.

### Purpose

Today answers:

- What should I know right now?
- What should I do today?
- Is anything important missing?
- How do I start the recommended workout quickly?

### Recommended Layout

Top-to-bottom:

1. Daily Grounded Recommendation
2. Recovery Check-In prompt/status
3. Today's Workout card
4. Quick Nutrition status/prompt
5. Optional compact recent workout/recovery context

### Daily Grounded Recommendation

Display near the top.

Show:

- daily coaching recommendation
- workout recommendation
- nutrition action
- rationale
- confidence/status label

Do not show raw internal fields in normal mode.

### Recovery Check-In Prompt

Recovery check-in should be prominent because it affects UserHealthState and workout guidance.

Tone should be gentle, not nagging.

Example copy:

> Complete today's recovery check-in to improve today's workout and nutrition guidance.

Possible states:

- Not completed today
- Completed today
- Recent but not today
- Unable to load

The user should be able to start or open the recovery check-in from Today.

### Today's Workout Card

The card should show the current recommended workout in one compact panel.

Include:

- workout title
- session focus
- estimated duration
- confidence/status label if useful
- exercise list
- sets/reps/RIR
- required equipment
- primary action button:
  - Generate Workout
  - Regenerate Workout
  - Select Workout
  - Start Workout
  - Continue Workout
  - Complete Workout

The button should reflect current state.

### Quick Nutrition Status/Prompt

Show a compact nutrition status area.

Examples:

- "No nutrition logged today yet."
- "Protein logged today; calories/carbs/fats still incomplete."
- "Nutrition targets are limited until logging is more complete."
- "Log food"

Do not show a full macro dashboard here unless it is compact and backend-approved.

## Workout Tab

Workout should combine:

- workout plan generation/preview
- selected workout
- active workout
- actual set logging
- substitutions
- planned-vs-actual review
- Exercise Catalog access

It should not feel like separate disconnected admin panels.

### Primary Workflow

The main workflow should be:

1. Generate/regenerate workout
2. Review workout
3. Apply optional substitutions
4. Start workout
5. Log sets
6. Complete workout
7. Review planned-vs-actual

### Recommended Workout Page Structure

Use compact workflow sections instead of many independent vertical panels.

Suggested layout:

1. Workout Controls
2. Current Workout
3. Active Set Logging
4. Workout Review
5. Exercise Catalog
6. Developer Details

### Generate/Regenerate Workout

Generate/regenerate should be one-click.

The user should not have to hunt through multiple panels.

Button labels:

- Generate Today's Workout
- Regenerate Workout
- Select This Workout
- Start Workout

### Current Workout Display

A normal workout session should clearly show:

- exercise
- planned sets
- planned reps
- target RIR
- target zone
- equipment
- weight used / actual weight
- actual reps
- actual RIR

The exact column order can change for readability.

Suggested columns:

| Exercise | Target | Zone | Equipment | Actual | Status |
| --- | --- | --- | --- | --- | --- |
| Dumbbell RDL | 3 x 8-10 @ RIR 2-3 | Main Lower | Dumbbell | 45 lb x 9 @ RIR 2 | Logged |

### Target Zone

Each planned exercise should have a friendly target zone label where possible:

- Main Lower / Primary Movement
- Main Push
- Main Pull
- Accessory / Core / Conditioning

Avoid calling the fourth slot a "finisher," especially for recovery_limited or data_quality_limited users.

### Active Workout Logging

Actual set logging should be in the workout flow, not hidden far below review/debug sections.

Logging should feel tied to the active exercise list.

For each exercise, the user should be able to log:

- set number
- actual reps
- actual weight
- actual RIR
- skipped
- notes

### Substitution Behavior

Substitutions should remain available but secondary.

They should appear inside the Workout flow near the planned exercise, not as a dominant standalone section.

Substitution display should show:

> Original: Romanian Deadlift
> Substituted with: Dumbbell RDL

Important follow-up:

After a substitution is applied during the Workout Plan step, actual set logging should automatically populate/use the substituted exercise more clearly.

Expected behavior:

- original planned exercise remains visible
- substituted exercise is clearly shown
- actual set logging defaults to the active substituted exercise
- completed actual sets use the substituted exercise name
- raw overlay details remain in Developer Mode

Substitution should not dominate the page.

## Nutrition Tab

Nutrition should be its own top-level tab.

### Purpose

Nutrition answers:

- what have I logged today?
- is logging complete enough?
- what nutrition guidance is approved today?
- how do I log food?

### Recommended Layout

1. Log Food
2. Today's Nutrition Summary
3. Backend-approved Nutrition Targets
4. Recent Nutrition History
5. Developer Details if enabled

### Rules

- Streamlit should only render backend-approved targets.
- Do not show calorie targets unless allowed by backend display flags.
- Do not show protein targets unless allowed by backend display flags.
- Do not show carbohydrate/fat targets unless allowed by backend display flags.
- If nutrition confidence is Limited, show the backend display message instead of a full macro table.

## History Tab

History should contain completed and recent activity, but it should not dominate the daily workflow.

Recommended content:

- recent workout executions
- completed workout review summaries
- planned-vs-actual compact summaries
- recent manual workouts if useful
- recent recovery/nutrition summaries later if useful

Detailed raw history payloads should be Developer Mode only.

## Reports Tab

Reports should contain:

- Generate Full AI Health Report
- Latest report
- Report history

Reports should not be the default daily workflow.

The daily grounded recommendation remains on Today because it is fast and deterministic.

Full reports can remain in Reports because they are heavier/slower.

## Developer Tab

Developer tab is optional if the global Developer Mode toggle is enough, but the requested top-level navigation includes Developer.

Developer should contain:

- raw JSON responses
- API route diagnostics
- plan instance IDs
- execution IDs
- session IDs
- runtime metadata
- report job metadata
- recommendation debug metadata
- internal reason codes
- raw planned-vs-actual payloads

Developer should be organized with expanders, not one giant dump.

## Planned-vs-Actual Review UX

The current planned-vs-actual review is too text-heavy.

Replace or supplement long text sections with:

- compact summary cards
- progress bars
- delta tables
- simple charts
- visual status labels

### Suggested Compact Sections

Use these sections, but avoid making each one a large vertical block:

1. Completion
2. Effort vs Plan
3. Reps vs Plan
4. Substitutions / Skips
5. Logging Quality

### Key Metrics

Show:

- completion_percentage
- planned_set_count
- actual_set_count
- completed_set_count
- skipped_set_count
- average_planned_rir
- average_actual_rir
- rir_deviation
- sets_below_planned_reps
- sets_inside_planned_reps
- sets_above_planned_reps
- deviation_flags

### Delta Display

Completed workout review should look similar to the workout session view, but with planned-vs-actual deltas.

Examples:

| Exercise | Planned | Actual | Rep Delta | Effort Delta | Status |
| --- | --- | --- | --- | --- | --- |
| DB Bench Press | 3 x 8-10 @ RIR 2-3 | 3 x 9 @ RIR 2 | 0 | On target | Complete |
| Cable Row | 3 x 10-12 @ RIR 2-3 | 2 x 8 @ RIR 1 | -2 sets / below reps | Harder | Partial |

User preference:

- show plus/minus differences
- less than planned can be yellow
- more than planned can be red
- language should remain neutral, not judgmental

### Flag Translation

Backend deviation flags should be translated into user-friendly labels.

Examples:

- incomplete_logging -> Some planned work has not been logged yet.
- actual_effort_harder_than_planned -> Logged effort was harder than planned.
- actual_effort_easier_than_planned -> Logged effort was easier than planned.
- skipped_exercises_present -> Some planned exercises were skipped.
- substitutions_present -> Some exercises were substituted.
- missing_actual_rir -> Some logged sets are missing RIR.
- missing_actual_reps -> Some logged sets are missing reps.
- reps_below_plan -> Some sets were below the planned rep range.
- reps_above_plan -> Some sets were above the planned rep range.

### Coaching Boundaries

The UI must avoid coaching conclusions beyond what the backend summary supports.

Do not imply:

- overtraining
- poor adherence
- automatic progression
- failed programming
- need for deload
- lack of effort

Use descriptive language instead:

- "Logged effort was harder than planned."
- "Some planned work was not logged."
- "This may need review if it repeats."

## Exercise Catalog Placement

Exercise Catalog should live inside Workout, likely in an expander or secondary subtab.

It should remain searchable and filterable, but it should not be a primary daily screen.

Suggested placement:

Workout tab:

- Current Workout
- Set Logging
- Workout Review
- Exercise Catalog Browser

The catalog should support:

- text search
- equipment filter
- movement pattern filter
- muscle group filter
- exercise type/category filter
- difficulty filter
- compatible-with-my-equipment toggle

Known future UX improvement:

- search aliases, such as "exercise ball" matching "stability ball"

## Data Display Rules

### Normal User Mode

Show:

- friendly labels
- compact summaries
- action buttons
- simple tables
- visual cues
- explanations written for a user

Hide:

- plan_instance_id
- execution_session_id
- workout_session_id
- raw enum names where friendly labels exist
- raw JSON
- internal reason codes
- debug flags
- raw backend payloads

### Developer Mode

May show everything, but organized.

## Implementation Sequencing After Spec Acceptance

### Milestone 1: Streamlit UX Redesign v2 — Today-first Layout

Goal:

Implement the new tab structure and Today landing page.

Scope:

- tabs: Today, Workout, Nutrition, History, Reports, Developer
- move Exercise Catalog inside Workout
- move Nutrition to top-level tab
- add Developer Mode toggle
- hide raw/debug details unless Developer Mode is enabled
- make Today the main landing page
- show Daily Grounded Recommendation, Recovery Check-In status, Today's Workout card, and Quick Nutrition status

### Milestone 2: Workout Flow UX v2

Goal:

Make Workout tab feel like one connected workflow.

Scope:

- Generate/regenerate workout
- Review workout
- Apply optional substitutions
- Start workout
- Log actual sets
- Complete workout
- Review planned-vs-actual

### Milestone 3: Workout Session Logging UX v2

Goal:

Make actual set logging feel like a workout app.

Scope:

- active exercise rows
- default log fields based on planned exercise
- substituted exercise auto-population
- compact set entry
- skipped set/exercise handling
- reduce vertical clutter

### Milestone 4: Planned-vs-Actual Visual Review v2

Goal:

Replace verbose planned-vs-actual sections with visual summary cards and delta table.

Scope:

- completion cards
- effort delta
- reps delta
- set completion
- substitutions/skips
- logging quality

### Milestone 5: Developer Mode Cleanup

Goal:

Move every raw/debug/internal display behind Developer Mode.

Scope:

- raw JSON
- API responses
- IDs
- runtime metadata
- internal reason codes
- debug payloads

## Acceptance Criteria

This spec is accepted when Architecture agrees that:

- Today is the default landing page.
- Top tabs are:
  - Today
  - Workout
  - Nutrition
  - History
  - Reports
  - Developer
- Exercise Catalog moves inside Workout.
- Nutrition is a top-level tab.
- Developer Mode owns raw/debug/internal detail.
- Workout flow becomes one connected workflow.
- Planned-vs-actual review becomes more visual and compact.
- Substitutions remain available but secondary.
- Actual set logging should clearly use substituted exercises after substitution.
- No backend behavior changes are required for this design milestone.

## Non-Goals

Do not add in this milestone:

- new backend schema
- CrewAI workout generation
- automatic progression
- weekly periodization
- nutrition redesign implementation
- report behavior changes
- recommendation response-shape changes
- workout generation redesign
- new persistence behavior
- new substitution backend behavior

## Final Design Statement

The next Streamlit implementation should make the app feel like a daily fitness companion.

The user should land on Today, see the recommendation, check recovery if needed, see the workout, start it, log it, complete it, and understand the result without scrolling through backend-style panels.

Developer details remain available, but normal user mode should feel clean, guided, and workout-first.
