# Versioning and compatibility

Free Exercise DB++ tracks two independent versions:

- `converterVersion` — mapping rules, evidence, classifications, and generator implementation.
- `schemaVersion` — the consumer-facing JSON contract.

Before 1.0, schema minor releases may add fields or enum values. Consumers should ignore unknown fields where practical.

An incompatible removal, rename, type change, or semantic change to a required field requires a schema major-version change.

Changes to exercise mappings, evidence, or classifications normally increment `converterVersion` without changing `schemaVersion`.

`exerciseId` values inherit the upstream Free Exercise DB IDs. If upstream removes or changes an ID, that is an upstream compatibility event and should be surfaced by CI and reviewed before release.

A release should publish the generated JSON, JSON Schema, converter version, upstream SHA-256, upstream exercise count, and audit summaries together.
