# DB++ interoperability audit

Review date: 2026-08-25. This document records capability, not an exporter. v1.2 maps stable DB++ concepts to the reviewed target and reports loss explicitly; v1.3 may add operational adapters.

Capability labels: `lossless`, `representable_with_conversion`, `representable_with_extension`, `lossy`, `unsupported`, `not_applicable`, `unknown`. A notes/metadata string is not treated as lossless support.

## Garmin FIT SDK FIT Profile and Workout/Activity file guides

Specification/API: current public FIT SDK documentation reviewed 2026-08-25.

FIT has Activity sessions and Workout/Workout Step prescriptions; set-like strength detail is profile/device dependent. Timestamps, duration, distance, repetitions and weight are representable with conversion. DB++ exerciseId, RIR, tempo, set type, laterality, substitutions, PLAN linkage and rep telemetry require developer fields or are unsupported. Custom developer data is the extension mechanism. Round-trip is normalized or lossy.

Authoritative reference: [https://developer.garmin.com/fit/overview/](https://developer.garmin.com/fit/overview/)

The official FIT SDK publishes strength exercise-name enums (for example, bench-press and squat exercise names). v1.2 uses the reviewed exact subset in [`mappings/garmin-fit-exercises.json`](../../mappings/garmin-fit-exercises.json) as its first production exercise identity crosswalk. The artifact is published under the Garmin FIT Protocol License; this release does not claim mappings for enum values not reviewed against DB++.

| DB++ concept | Assessment |
|---|---|
| identity/name/custom exercise | lossy or extension_required |
| timestamps/time zones/provenance | representable_with_conversion |
| ACTUAL occurrence, reps, load, duration, distance | representable_with_conversion where target fields exist |
| RPE/RIR/tempo/set type/laterality/substitution | extension_required, lossy, or unsupported |
| PLAN, arbitrary cycles, progression, TARGET | unsupported or target-specific extension |
