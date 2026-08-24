# Garmin FIT mapping (draft 0.1.0)

This document defines the first declarative mapping from DB++ Workout 0.2 observations to Garmin FIT concepts. It is a translation layer, not a change to either native schema. The normative entries are in [`mappings/garmin-fit.json`](../mappings/garmin-fit.json).

Garmin FIT distinguishes Activity files (recorded sessions) from Workout files (prescribed structured activities). This mapping targets Activity files because DB++ Workout stores observations. A FIT export should include the required File Id and session summary messages; Garmin’s official documentation states that Activity files use Session/Lap summaries and that File Id is required.

## Quality labels

- `exact`: the source value has a direct FIT counterpart with no semantic loss.
- `compatible`: conversion is required but the meaning is retained.
- `lossy`: FIT can carry an approximation or display value, but not the full DB++ semantics.
- `extension_required`: use FIT developer data or an application sidecar to preserve the value.
- `unsupported`: no mapping is claimed; omit it rather than inventing a value.

## Policy

DB++ `exerciseId` remains the source-of-truth identity. Garmin activity/category enums and display names are optional target hints and must never replace it. Quantity units are converted to FIT’s expected units (kilograms, metres, and integer milliseconds) only when the conversion is unambiguous. Missing values remain missing. RPE, RIR, failure, laterality, macro-segments, and rep telemetry are independent observations; one is not inferred from another.

One observed set is represented by the closest available FIT Lap grouping. This is compatible for basic reps/load/duration/distance, but set completion and structure grouping are lossy. Drop sets, rest-pause sets, cluster sets, custom exercise IDs, and rep-level telemetry require developer fields or a sidecar to round-trip. A consumer that does not understand those fields may safely ignore them while retaining the ordinary activity summary.

## Scope and limitations

This phase provides reviewed declarative mappings only. It does not encode/decode binary FIT, claim Garmin Connect import acceptance, or claim a universal strength-training FIT profile across devices. Implementers must validate generated files with the FIT SDK/profile version they target. Garmin’s FIT profile is versioned and product profiles can support different subsets of messages.

References: [Garmin FIT file types](https://developer.garmin.com/fit/file-types), [FIT Activity files](https://developer.garmin.com/fit/file-types/activity/), and [FIT protocol](https://developer.garmin.com/fit/protocol/).
