# 1.0 consumer contract

The following contract is stable as of **v1.0.0**:

- the top-level `metadata` and `exercises` objects;
- `exerciseId` as the stable foreign key, inherited from upstream Free Exercise DB;
- the muscle ontology identifiers;
- `annotation.direct`, `annotation.indirect`, and `annotation.stabilizers`;
- set credits of direct `1.0`, indirect `0.5`, stabilizer `0.0`;
- `annotation.volumeEligible`;
- confidence values `high`, `medium`, `low`;
- embedded evidence references and movement-pattern evidence status;
- the single-file runtime property: consumers do not need sidecar mapping files.

After v1.0.0, incompatible changes to this contract require a new major release.
Compatible additive fields, evidence updates, mapping corrections, and reviewed upstream
additions may ship in minor or patch releases as appropriate.

## Release, converter, and schema versions

The Git tag/release version, `converterVersion`, and `schemaVersion` are intentionally independent:

- the Git release version identifies the public project release;
- `converterVersion` identifies the mapping/generator implementation;
- `schemaVersion` identifies the JSON data-contract revision.

A v1.x project release therefore does not require the converter or schema version strings
to also be `1.x` when those respective contracts have not changed.

## Upstream IDs

An upstream addition is allowed only after the generated mapping/audit output is reviewed.
An upstream removal or ID rename is a compatibility event and fails CI until explicitly handled.

## Medium confidence

Medium confidence is a supported part of the 1.0 contract. It means uncertainty is explicit,
not unresolved. Permitted reasons are complex movement bookkeeping, indirect evidence, or a
deliberately retained named fallback.
