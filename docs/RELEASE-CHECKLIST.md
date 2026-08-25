# Release checklist

## Build and contracts

- [ ] Full generated DB build is reproducible and matches the reviewed upstream source SHA-256.
- [ ] Generated DB validates against free-exercise-db-plusplus.schema.json.
- [ ] Workout, Workout PLAN, TARGET, and interop mapping schemas validate.
- [ ] Reports are regenerated and generated outputs are committed.
- [ ] Needs review is zero; no used pattern has provisional evidence; medium mappings are explained.

## Semantic and package gates

- [ ] Release-contract, golden-mapping, medium-policy, semantic-hardening, PLAN coverage, PLAN-vs-PLAN, PLAN-vs-ACTUAL, and research-export tests pass.
- [ ] Full root Python suite and Python consumer package tests pass.
- [ ] An isolated Python wheel installs/imports and runs a real PLAN analysis outside the checkout.
- [ ] Swift, Kotlin, and R package tests pass.
- [ ] Interop mapping registry validation passes.
- [ ] Canonical PLAN, ACTUAL, and TARGET examples validate.

## Release execution

- [ ] README, methodology, compatibility, versioning, analysis semantics, and release notes are current.
- [ ] Human commit release: prepare v1.1.0 is identified separately from any build: regenerate Free Exercise DB++ [skip ci] commit.
- [ ] Working tree is clean before tagging.
- [ ] Annotated v1.1.0 points directly to the human release-preparation commit, not a bot commit.
- [ ] Tag-triggered release workflow validates the reviewed upstream snapshot.
- [ ] Release contains the DB, all public schemas, SHA256SUMS, and release documentation.
- [ ] Published assets, checksums, release body, tag target, raw main URLs, release URLs, and a released-artifact Python quick start are verified.
