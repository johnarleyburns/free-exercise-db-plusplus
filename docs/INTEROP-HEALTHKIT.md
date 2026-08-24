# Apple HealthKit mapping (draft 0.1.0)

This document defines a declarative mapping from DB++ Workout 0.2 to Apple HealthKit. The normative entries are in [`mappings/healthkit.json`](../mappings/healthkit.json). It is an interoperability translation layer; it does not alter the DB++ workout contract.

## Model and policy

HealthKit’s `HKWorkout` is a session-level record with start/end dates, activity type, optional duration, distance, active energy, device, events, and metadata. Additional quantity samples can be associated with a workout. Consequently, HealthKit is treated as a summary/export surface. The DB++ workout JSON remains the source of truth for exercise identity, sets, reps, load, RPE/RIR, laterality, structures, macro-segments, and rep telemetry.

The mapping preserves `sessionId` and DB++ exercise IDs through stable or namespaced metadata where permitted. A HealthKit activity type must not be guessed from an exercise name. Workout 0.2 does not define a normative total-energy or session activity-type field, so those mappings are explicitly unsupported rather than derived.

## Quality labels

- `exact`: direct semantic counterpart.
- `compatible`: counterpart exists after unit or representation conversion.
- `lossy`: HealthKit can retain only a summary or approximation.
- `extension_required`: namespaced metadata or a sidecar is required to round-trip the source value.
- `unsupported`: no mapping is claimed.

## Export behavior

An exporter should create an `HKWorkout` only when the source has a valid end time or an explicit application policy for open sessions. Distance is written only to an activity-appropriate `HKQuantityTypeIdentifier`; it must not be mislabeled as walking/running distance for strength work. Active energy is written only when supplied by an authoritative source, never calculated from DB++ load or reps.

HealthKit may condense or coalesce quantity samples, and consumers may ignore custom metadata. Therefore round-trip fidelity is intentionally limited: retain the original DB++ JSON alongside or linked to the HealthKit workout. No HealthKit import/export implementation is included in this phase.

References: [Apple HKWorkout](https://developer.apple.com/documentation/healthkit/hkworkout), [HKQuantityTypeIdentifier](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier), [active energy burned](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/activeenergyburned), and [distance walking/running](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/distancewalkingrunning).
