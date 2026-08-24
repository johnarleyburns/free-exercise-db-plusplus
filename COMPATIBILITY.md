# 1.0 consumer contract

The following are intended to become stable at 1.0:

- the top-level `metadata` and `exercises` objects;
- `exerciseId` as the stable foreign key, inherited from upstream Free Exercise DB;
- the muscle ontology identifiers;
- `annotation.direct`, `annotation.indirect`, and `annotation.stabilizers`;
- set credits of direct `1.0`, indirect `0.5`, stabilizer `0.0`;
- `annotation.volumeEligible`;
- confidence values `high`, `medium`, `low`;
- embedded evidence references and movement-pattern evidence status;
- the single-file runtime property: consumers do not need sidecar mapping files.

After 1.0, incompatible changes to this contract require a major version.

## Upstream IDs

An upstream addition is allowed only after the generated mapping/audit output is reviewed.
An upstream removal or ID rename is a compatibility event and fails CI until explicitly handled.

## Medium confidence

Medium confidence is a supported part of the 1.0 contract. It means uncertainty is explicit, not unresolved.
Permitted reasons are complex movement bookkeeping, indirect evidence, or a deliberately retained named fallback.
