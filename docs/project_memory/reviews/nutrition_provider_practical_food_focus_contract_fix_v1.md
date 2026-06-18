# Nutrition Provider Practical Food Focus Contract Fix v1 Review

## Decision

Implemented as a narrow provider contract and validation tuning fix.

## Reason for change

Diagnostic Matrix QA Retry v1 showed all rejected provider candidates were concentrated in practical_food_focus.

The provider was not failing randomly. The repeated field-level failures indicate that the approved food suggestion contract was not explicit enough for qwen2.5 and/or the validator boundary.

## Implementation summary

The practical_food_focus validation path now supports two safe modes:

1. Approved food suggestions exist:
   - exact approved food names are allowed
   - exact approved gram values are allowed only when backend supplied them
   - generic approved-list language is allowed
   - invented foods remain rejected

2. Approved food suggestions do not exist:
   - safe limitation language is allowed
   - logging-completeness-first language is allowed
   - suggestion availability/action language remains rejected

The direct-Ollama Nutrition prompt now makes these rules explicit.

## Risk assessment

Risk is low because this does not relax the core food suggestion boundary. It narrows the accepted language to approved food suggestions or explicit no-suggestion limitation language.

## Runtime QA required

Yes.

The next QA pass should rerun users 101-105 with qwen2.5:3b and compare approval/fallback distribution and diagnostics against the prior matrix.
