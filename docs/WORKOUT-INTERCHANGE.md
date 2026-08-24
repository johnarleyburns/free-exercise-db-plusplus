# Workout interchange schema

Workout schema `0.2.0`/`0.3.0` is the portable observation format for resistance-training sessions. It stores what happened; effective sets, tonnage, and muscle-volume analytics remain derived outputs using the stable DB++ exercise database.

## 0.2 highlights

- ACTUAL 0.2.0 remains accepted for transition; new PLAN-linked records use `schemaVersion: "0.3.0"`.
- PLAN linkage is optional: `planReference` belongs to the session, `exercisePrescriptionId` and `substitution` to exercise observations, and `setPrescriptionId` to sets.
- Standalone ACTUAL records remain valid without any PLAN fields.
- Measurements use `{ "value": number, "unit": string }` quantities.
- DB++ exercises use `exerciseId`; unmapped exercises use `exerciseName` and may include an `externalExerciseId`.
- `laterality` is available on exercises, sets, and macro-segments.
- Supersets, tri-sets, giant sets, circuits, complexes, and paired work use `structure`; they are not set types.
- Drop, rest-pause, and cluster work uses `segments` inside one set. Individual rep telemetry remains optional in `repetitions`.
- Resistance modes explicitly distinguish bodyweight, external load, assistance, bands, and machine settings.

## Migration from 0.1 and 0.2

Migration is forward-only. The reference migrator at `src/workout/migrate_workout.py` supports `0.1.x -> 0.2.0 -> 0.3.0`; the 0.2-to-0.3 step only changes the version and preserves unknown fields/extensions. Add PLAN links only when a real PLAN revision exists; migration never invents them. The 0.1-to-0.2 step adds `laterality` where useful and converts scalar measurements to quantity objects. The old `setType: "drop"` remains valid; intra-set drops should additionally be represented with `segments`. The old `repObservation.velocity` name is migrated to `meanVelocity`, and scalar range-of-motion values become metre quantities. Consumers should reject unsupported future versions rather than silently downgrading.

See the complete valid matrix under `examples/workouts/` and deliberately invalid cases under `fixtures/workout/`.
