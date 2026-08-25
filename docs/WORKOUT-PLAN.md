# Workout PLAN 0.1 and 0.2

`workout-plan.schema.json` is the prescription counterpart to the Workout ACTUAL
`workout.schema.json` 0.2.0/0.3.0 contract. PLAN describes what is intended; ACTUAL records
what happened. They are separate artifacts and must not be merged.

## Identity and cycle

Every plan has a conceptual `planId` and immutable prescription `revisionId`. A native
cycle declares its length in days, so eight-day rotations and research protocols do not
need to pretend to be calendar weeks. Analysis may later derive a seven-day equivalent,
but PLAN stores only the native prescription.

Each planned session has a stable `planSessionId` and a non-negative `dayOffset` within
the cycle. Each exercise occurrence has its own stable `prescriptionId`, even when the
same DB++ `exerciseId` appears more than once.

## Prescriptions

A prescription must identify either a known DB++ `exerciseId` or a custom
`exerciseName`; an optional `externalExerciseId` preserves an app or study identifier.
`sets` and `reps` accept an exact non-negative integer or a range with any combination
of `min`, `target`, and `max`. The deterministic validator rejects ranges where
`min > target > max` ordering is violated.

`load` accepts a quantity such as `{ "value": 80, "unit": "kg" }` or a ranged
quantity with a shared unit. `effort` may prescribe RPE (0–10) or non-negative RIR,
exactly or as ranges. These fields describe intent, not measured outcomes.

Neither PLAN version stores DB++ muscle roles, effective-set totals, or other derived coverage. PLAN 0.2 adds ordered phases with `durationCycles`, optional phase-specific cycles, heterogeneous `plannedSets` with stable `setPrescriptionId` values, declarative progression metadata, and optional or conditional prescriptions. Progression remains descriptive metadata, not executable scripting. PLAN-vs-ACTUAL links remain in ACTUAL 0.3, and external exporters remain separate interoperability tooling.

## Validation

The reference validator requires Python and `jsonschema`:

```bash
python src/plan/validate_plan.py examples/plans/basic-upper-lower.json
```

It performs Draft 2020-12 schema validation plus deterministic semantic checks for
duplicate session, prescription, phase, and planned-set IDs; phase references; and range ordering. Valid examples are under
`examples/plans/`; deliberately invalid fixtures are under
`fixtures/plan/invalid/`.

## Revision policy

Once ACTUAL observations reference a plan revision, do not mutate that revision in
place. Create a new `revisionId` so historical adherence analysis can recover the
exact prescription that was in force.

## Version and prescription-style rules

PLAN 0.1 documents cannot use 0.2-only phases, phase links, planned sets, progression, or optional/conditional fields. PLAN 0.2 supports them. Each exercise uses exactly one prescription style: aggregate `sets` plus `reps` (with optional aggregate load/effort), or explicit `plannedSets`; mixing the styles is invalid.
