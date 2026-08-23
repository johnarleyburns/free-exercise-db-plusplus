# Versioning and compatibility

DB++ has two versions: `converterVersion` for rules/implementation and `schemaVersion` for the consumer-facing JSON contract.

Before 1.0, schema minor versions may add fields or enum values; consumers should ignore unknown fields where practical. Incompatible removal/renaming/type or semantic changes require a schema major-version change.

Mapping, evidence, or classification changes normally increment `converterVersion` without changing the schema. Stable `exerciseId` values inherit upstream IDs; upstream ID changes are compatibility events that must be surfaced for review.

A release should publish the generated JSON, schema, upstream SHA-256, converter version, and audits together.
