# DB++ interoperability audit

Review date: 2026-08-25. This document records capability, not an exporter. v1.2 maps stable DB++ concepts to the reviewed target and reports loss explicitly; v1.3 may add operational adapters.

Capability labels: `lossless`, `representable_with_conversion`, `representable_with_extension`, `lossy`, `unsupported`, `not_applicable`, `unknown`. A notes/metadata string is not treated as lossless support.

## Android Health Connect

`ExerciseSessionType` values such as strength training and weightlifting are session/activity categories, not individual exercise identities. The canonical artifact is [`mappings/health-connect-exercises.json`](../../mappings/health-connect-exercises.json) with `mappingKind: category`; it intentionally contains category compatibility metadata only. It must not be used to return DB++ exercise identity candidates. Health Connect has no reviewed individual strength-exercise vocabulary in this release, so it is not an identity crosswalk.

Specification/API: Jetpack Health Connect 1.1.0 workout guide; Android API reference reviewed 2026-08-25.

ExerciseSessionRecord provides timestamps, session type, segments, laps, metadata, device and zone offsets. PlannedExerciseSessionRecord supports PLAN-like planned blocks where feature availability permits. Repetitions, load, RPE/RIR, set order, laterality, substitutions and DB++ exercise identity are not guaranteed standard fields; use an extension only where permitted.

Authoritative reference: [https://developer.android.com/health-and-fitness/health-connect/experiences/workouts](https://developer.android.com/health-and-fitness/health-connect/experiences/workouts)

| DB++ concept | Assessment |
|---|---|
| identity/name/custom exercise | lossy or extension_required |
| timestamps/time zones/provenance | representable_with_conversion |
| ACTUAL occurrence, reps, load, duration, distance | representable_with_conversion where target fields exist |
| RPE/RIR/tempo/set type/laterality/substitution | extension_required, lossy, or unsupported |
| PLAN, arbitrary cycles, progression, TARGET | unsupported or target-specific extension |
