# Versioning and compatibility

Free Exercise DB++ tracks three related but independent versions:

- **Git release version** — the public project release, e.g. `v1.0.0`.
- **`converterVersion`** — mapping rules, evidence, classifications, and generator implementation.
- **`schemaVersion`** — the consumer-facing JSON contract revision.

## Project releases

Free Exercise DB++ uses semantic versioning for Git releases.

After v1.0.0:

- **major** releases contain incompatible changes to the stable consumer contract;
- **minor** releases may add compatible capabilities, fields, classifications, or reviewed upstream coverage;
- **patch** releases contain compatible corrections to mappings, evidence, documentation, tooling, or release infrastructure.

The converter and schema versions do not need to numerically match the Git release version.

## Schema compatibility

An incompatible removal, rename, type change, or semantic change to a required consumer field
requires both an appropriate schema-contract revision and a new major project release.

Compatible additive fields may be introduced in a non-major release. Consumers should ignore
unknown fields where practical.

## Mapping and evidence changes

Changes to exercise mappings, evidence, or classifications normally increment
`converterVersion` without requiring a `schemaVersion` change when the JSON contract is unchanged.

## Exercise IDs

`exerciseId` values inherit upstream Free Exercise DB IDs. If upstream removes or changes an ID,
that is a compatibility event and must be surfaced by CI and reviewed before release.

## Release artifacts

A release publishes the generated JSON, JSON Schema, workout schema, SHA-256 checksums, and the
methodology/compatibility/evidence documentation together.
