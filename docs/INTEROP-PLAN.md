# PLAN interoperability

PLAN and ACTUAL are distinct source artifacts. Mapping registries now declare
`sourceArtifact` as `workout-plan`, `workout-actual`, or `exercise-db`. Existing FIT,
HealthKit, and Health Connect registries remain ACTUAL-oriented.

`mappings/fhir-plan.json` is the first PLAN mapping profile. It documents a deliberate
FHIR-oriented translation of plan/revision identity, native cycle length, planned sessions,
DB++ exercise IDs, ranged prescriptions, and descriptive progression metadata. Fields
without a direct FHIR representation are marked `extension_required` or `lossy`; no
exporter silently mutates PLAN semantics.

FHIR is the first serious PLAN candidate because its intent/definition resources can
represent prescriptions separately from observations. FIT, HealthKit, and Health Connect
should continue to treat DB++ PLAN as the high-fidelity source when their APIs are
primarily observation/device-oriented.
