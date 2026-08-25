# Interoperability

v1.2 establishes audited capability mappings and a public identity registry. It does not provide FIT, HealthKit, Health Connect, FHIR, or Google Fit file conversion; operational import/export is v1.3.

The first production identity crosswalk is Android Health Connect. Its official exercise-session vocabulary is intentionally published as two explicit `unmapped` records: session categories are broader than DB++ exercise identities. Garmin FIT is the first reviewed structural ACTUAL mapping.

Identity relations are `exact`, `close`, `broader`, `narrower`, `approximate`, and `unmapped`. Direction is `external_to_dbpp`, `dbpp_to_external`, or `bidirectional`; confidence is `high`, `medium`, or `low`.

See the [compatibility matrix](COMPATIBILITY-MATRIX.md), [schemas](../../exercise-interop-mapping.schema.json), and [coverage reports](../../reports/interop/).
