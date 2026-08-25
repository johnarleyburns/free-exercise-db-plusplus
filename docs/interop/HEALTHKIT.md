# DB++ interoperability audit

Review date: 2026-08-25. This document records capability, not an exporter. v1.2 maps stable DB++ concepts to the reviewed target and reports loss explicitly; v1.3 may add operational adapters.

Capability labels: `lossless`, `representable_with_conversion`, `representable_with_extension`, `lossy`, `unsupported`, `not_applicable`, `unknown`. A notes/metadata string is not treated as lossless support.

## Apple HealthKit

Specification/API: Current Apple Developer HealthKit documentation reviewed 2026-08-25.

HKWorkout provides activity type, start/end, duration, events, metadata and associated quantity samples. Custom metadata is available, but no standard resistance set/exercise identity vocabulary is assumed. Reps/load/RPE/RIR/set type/laterality and PLAN linkage are extension or unsupported.

Authoritative reference: [https://developer.apple.com/documentation/healthkit/hkworkout](https://developer.apple.com/documentation/healthkit/hkworkout)

| DB++ concept | Assessment |
|---|---|
| identity/name/custom exercise | lossy or extension_required |
| timestamps/time zones/provenance | representable_with_conversion |
| ACTUAL occurrence, reps, load, duration, distance | representable_with_conversion where target fields exist |
| RPE/RIR/tempo/set type/laterality/substitution | extension_required, lossy, or unsupported |
| PLAN, arbitrary cycles, progression, TARGET | unsupported or target-specific extension |
