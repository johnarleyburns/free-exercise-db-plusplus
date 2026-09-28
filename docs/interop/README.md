# Interoperability

v1.2 establishes audited capability mappings and a public identity registry. v1.3
adds operational FHIR conversion and loss-aware health-data envelopes. Native FIT,
HealthKit, and Health Connect records still require their platform SDKs and a
retained DB++ sidecar; see [the full adapter guide](HEALTH-DATA-ADAPTERS.md).

Health Connect `ExerciseSessionType` is published only as a structural/category artifact. Its session categories are broader than DB++ exercise identities, so no Health Connect exercise identity crosswalk is advertised. Garmin FIT is the first reviewed production exercise identity crosswalk; its FIT strength exercise-name enums provide individual exercise concepts and the published entries are limited to reviewed exact matches. Garmin’s broader FIT field mapping remains a separate structural artifact.

Identity relations are `exact`, `close`, `broader`, `narrower`, `approximate`, and `unmapped`. Direction is `external_to_dbpp`, `dbpp_to_external`, or `bidirectional`; confidence is `high`, `medium`, or `low`.

See the [compatibility matrix](COMPATIBILITY-MATRIX.md), [schemas](../../exercise-interop-mapping.schema.json), and [coverage reports](../../reports/interop/).
