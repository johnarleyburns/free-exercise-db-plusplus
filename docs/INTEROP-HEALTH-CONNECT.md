# Android Health Connect mapping (draft 0.1.0)

This document defines a declarative mapping from DB++ Workout 0.2 to Android Health Connect. The normative entries are in [`mappings/health-connect.json`](../mappings/health-connect.json). This is a translation layer, not a change to the native DB++ schemas.

## Model and policy

Health Connect represents a workout with `ExerciseSessionRecord`. It supports associated records such as `DistanceRecord` and `ActiveCaloriesBurnedRecord`, and current APIs provide `ExerciseSegment` intervals with optional repetitions, weight, set index, and perceived exertion. These capabilities make Health Connect more expressive for basic set summaries than generic session-only stores, but it is still not a lossless DB++ strength log.

DB++ remains the source of truth for stable exercise IDs, custom exercises, load semantics, laterality, structures, macro-segments, RIR/failure, and rep telemetry. Health Connect exercise-type constants are target hints, never replacements for DB++ identity. Preserve IDs through client record identifiers and namespaced metadata where needed.

## Quality labels

- `exact`: direct semantic counterpart.
- `compatible`: conversion or interval construction is required, but meaning is retained.
- `lossy`: only a summary/approximation is available.
- `extension_required`: namespaced metadata or a sidecar is needed for round-trip fidelity.
- `unsupported`: no mapping is claimed.

## Export behavior

`ExerciseSessionRecord` requires start and end times, so an open DB++ session needs an explicit application policy before export. Each source set may become an `ExerciseSegment` when timestamps can be assigned; otherwise the exporter must document its interval policy. Reps, weight, set number, and RPE map to segment fields when the target API/version supports them. Bodyweight, assisted, band, and machine-setting resistance must not be silently encoded as external kilograms.

Distance uses `DistanceRecord` only for an appropriate activity. Active calories are written only when an authoritative source supplies them; they are never calculated from DB++ observations. Drop/rest-pause/cluster segments, laterality, and rep telemetry require metadata or a sidecar. Keep the original DB++ JSON linked by `clientRecordId` for high-fidelity round trips.

This phase provides declarative mappings only. It does not implement Kotlin import/export, claim permission grants, or guarantee behavior across all Health Connect API versions and device providers.

References: [Develop workout experiences with Health Connect](https://developer.android.com/health-and-fitness/health-connect/experiences/workouts), [ExerciseSessionRecord](https://developer.android.com/reference/androidx/health/connect/client/records/ExerciseSessionRecord), [ExerciseSegment](https://developer.android.com/reference/androidx/health/connect/client/records/ExerciseSegment), [Record metadata](https://developer.android.com/reference/androidx/health/connect/client/records/metadata/Metadata), and [DistanceRecord](https://developer.android.com/reference/androidx/health/connect/client/records/DistanceRecord).
