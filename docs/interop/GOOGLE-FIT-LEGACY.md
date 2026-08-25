# DB++ interoperability audit

Review date: 2026-08-25. This document records capability, not an exporter. v1.2 maps stable DB++ concepts to the reviewed target and reports loss explicitly; v1.3 may add operational adapters.

Capability labels: `lossless`, `representable_with_conversion`, `representable_with_extension`, `lossy`, `unsupported`, `not_applicable`, `unknown`. A notes/metadata string is not treated as lossless support.

## Google Fit REST activity and exercise data types

Specification/API: Legacy REST activity-types and activity data documentation reviewed 2026-08-25.

Google Fit exposes broad activity types and an exercise data type with repetitions, duration and resistance concepts. It is historical context only; deprecation/lifecycle must be checked by adapters. DB++ identity, RIR, PLAN and detailed set semantics remain lossy or unsupported.

Authoritative reference: [https://developers.google.com/fit/rest/v1/reference/activity-types](https://developers.google.com/fit/rest/v1/reference/activity-types)

| DB++ concept | Assessment |
|---|---|
| identity/name/custom exercise | lossy or extension_required |
| timestamps/time zones/provenance | representable_with_conversion |
| ACTUAL occurrence, reps, load, duration, distance | representable_with_conversion where target fields exist |
| RPE/RIR/tempo/set type/laterality/substitution | extension_required, lossy, or unsupported |
| PLAN, arbitrary cycles, progression, TARGET | unsupported or target-specific extension |
