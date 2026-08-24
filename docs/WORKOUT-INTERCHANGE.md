# Workout interchange schema

Workout schema `0.2.0` is the portable observation format for resistance-training sessions. It stores what happened; effective sets, tonnage, and muscle-volume analytics remain derived outputs using the stable DB++ exercise database.

## 0.2 highlights

- Every session declares `schemaVersion: "0.2.0"`.
- Measurements use `{ "value": number, "unit": string }` quantities.
- DB++ exercises use `exerciseId`; unmapped exercises use `exerciseName` and may include an `externalExerciseId`.
- `laterality` is available on exercises, sets, and macro-segments.
- Supersets, tri-sets, giant sets, circuits, complexes, and paired work use `structure`; they are not set types.
- Drop, rest-pause, and cluster work uses `segments` inside one set. Individual rep telemetry remains optional in `repetitions`.
- Resistance modes explicitly distinguish bodyweight, external load, assistance, bands, and machine settings.

## Migration from 0.1

Migration is forward-only. Change the version to `0.2.0`, add `laterality` where useful, and convert any scalar measurement to a quantity object. The reference migrator at `src/workout/migrate_workout.py` is deterministic and preserves unknown fields/extensions. The old `setType: "drop"` remains valid; intra-set drops should additionally be represented with `segments`. The old `repObservation.velocity` name is migrated to `meanVelocity`, and scalar range-of-motion values become metre quantities. Consumers should reject unsupported future versions rather than silently downgrading.

See the complete valid matrix under `examples/workouts/` and deliberately invalid cases under `fixtures/workout/`.
