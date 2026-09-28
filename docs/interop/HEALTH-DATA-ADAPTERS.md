# Full health-data adapters

This project treats “full import/export” as a lossless DB++ round trip, not as
a claim that the target platform has an equivalent strength-training schema.
Every adapter therefore has two outputs:

1. a target-native projection for the fields the target understands; and
2. an exact DB++ ACTUAL sidecar, retained with the target record.

Without the sidecar, a strict import must fail rather than silently discard
exercise identity, resistance mode, set type, laterality, structures,
segments, RPE/RIR, tempo, failure, velocity, range of motion, or provenance.

## Garmin FIT

Use Garmin’s official FIT SDK for binary encoding/decoding. Garmin publishes C,
Swift, Objective-C++, Java, C#, JavaScript, and Python SDKs; the C, Swift, and
Objective-C++ SDKs support both decoding and encoding. The DB++ mapping targets
an **Activity** file because ACTUAL is an observation record. A valid activity
file needs a File Id, Activity, Session, and required summary timestamps.

The normal projection is:

- `Session` for the DB++ session summary;
- `Lap` groups for set/exercise boundaries where the device profile permits;
- `Record` messages for time-series observations;
- FIT Developer Data fields for DB++ IDs and fields without standard FIT
  equivalents; and
- a namespaced canonical-workout sidecar for guaranteed round trips.

Garmin’s Developer Data Fields are self-describing and can be attached to
existing FIT messages, but FIT profile/device support still varies. FIT SDK
protocol v2 is required when developer fields are emitted. Generated files
must be validated against the specific FIT profile/SDK version being targeted.

Official references: [FIT SDKs](https://developer.garmin.com/fit/get-the-sdk/),
[FIT file types](https://developer.garmin.com/fit/file-types/),
[Activity files](https://developer.garmin.com/fit/articles/file-types/activity.html),
[FIT protocol](https://developer.garmin.com/fit/articles/fit-protocol/fit_protocol.html),
and [Developer Data Fields](https://developer.garmin.com/fit/cookbook/developer-data).

## Apple HealthKit

HealthKit is an on-device API, not an import/export file format. Use
`HKWorkoutBuilder` to create a workout, `finishWorkout` to save it, and
`HKSampleQuery`/workout queries to read it. The activity type should be chosen
explicitly; DB++ must not infer it from an exercise name. The supported
strength categories are `traditionalStrengthTraining` and
`functionalStrengthTraining`.

The target projection is an `HKWorkout` summary plus metadata. HealthKit has no
standard per-set resistance-training identity vocabulary, so the exact DB++
JSON must be retained in metadata or, preferably, in application storage keyed
by the HealthKit workout UUID. Quantity samples may be added for authoritative
distance or energy data only; those values must not be invented from sets or
load.

Apps must request explicit read/write authorization and include the HealthKit
capability and usage descriptions. The Swift adapter in this repository stores
the canonical JSON in metadata and exposes a query that returns only records
with a DB++ sidecar.

Official references: [authorization](https://developer.apple.com/documentation/healthkit/authorizing-access-to-health-data),
[`HKWorkoutBuilder`](https://developer.apple.com/documentation/healthkit/hkworkoutbuilder),
[`HKWorkoutActivityType`](https://developer.apple.com/documentation/healthkit/hkworkoutactivitytype),
and [HealthKit metadata](https://developer.apple.com/documentation/healthkit/hkobject/metadata).

## Android Health Connect

Health Connect is also an on-device, permissioned API rather than a portable
file format. Use `HealthConnectClient`, request the narrowest required
permissions, and read/write `ExerciseSessionRecord`. DB++ sets map to
`ExerciseSegment` where possible: repetitions, weight, set index, and RPE are
available in current APIs. Session timestamps, exercise category, metadata,
and optional routes are represented separately.

Health Connect has no DB++ exercise-ID namespace. Preserve DB++ identity and
the complete ACTUAL in application storage keyed by `Metadata.clientRecordId`
and the record UUID. Do not encode bodyweight, assistance, bands, or machine
settings as kilograms. Route reads can require deliberate user consent, and
historical/background reads have additional permissions and availability
constraints.

Official references: [workout experiences](https://developer.android.com/health-and-fitness/health-connect/experiences/workouts),
[`ExerciseSegment`](https://developer.android.com/reference/androidx/health/connect/client/records/ExerciseSegment),
[`HealthConnectClient`](https://developer.android.com/reference/androidx/health/connect/client/HealthConnectClient),
[permissions](https://developer.android.com/health-and-fitness/health-connect/data-types),
and [exercise routes](https://developer.android.com/health-and-fitness/health-connect/features/exercise-routes).

## Language status

| Language | Current support in this change | Native SDK boundary |
|---|---|---|
| Python | Lossless sidecar envelopes and strict/allow-lossy import/export projections for all three targets | Garmin binary SDK and platform APIs remain host dependencies |
| Swift | Same envelope plus a real conditional HealthKit adapter; FIT is injectable through the official Garmin Swift SDK boundary | Add Garmin’s `FITSwiftSDK` to the host app; HealthKit exists only on Apple platforms |
| Kotlin/JVM | Lossless Health Connect envelope and projection model | Android `HealthConnectClient` must be supplied by an Android host; the current artifact is JVM-only |
| R | Lossless sidecar envelope helpers for analysis/research workflows | Native mobile SDK access is outside R’s package boundary |
| C | Portable sidecar ABI in `packages/c`; native projection is host-provided | Add Garmin’s official FIT C SDK and an Apple/Android host bridge for native records |

The Python and Swift adapters intentionally reject native-only records in
strict mode. This is the only safe default for a “full DB++ health data” import.
