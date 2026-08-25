# Changelog

## v1.1.0

### Added

- Workout ACTUAL and PLAN interchange guidance, canonical examples, and public Python package examples.
- Volume TARGET profiles and comparisons against PLAN effective-set coverage.
- PLAN coverage for direct, indirect, stabilizer, effective-set, and movement-pattern exposure.
- Arbitrary native plan cycles, explicit seven-day normalization, independent min/target/max ranges, and periodized phases.
- PLAN-vs-PLAN comparison, exposure-frequency reporting, deterministic research CSV output, and explicit provenance metadata.

### Stabilized

- PLAN-vs-ACTUAL matching with explicit substitutions and setPrescriptionId handling.
- Unplanned ACTUAL work, strict prescription adherence, substitution-adjusted completion, and missing-work diagnostics.
- Separate direct, indirect, stabilizer, effective-set, load, RPE, RIR, and meaningful volume-load adherence dimensions.
- TARGET gap analysis and the named dbpp-default-volume-v1 analysis policy.

### Analysis semantics

- Set credits remain authoritative in database metadata; shipped defaults are direct 1.0, indirect 0.5, and stabilizer 0.0.
- volumeEligible, counted set types, range preservation, cycle normalization, phase weighting, substitutions, and provenance are covered by semantic-hardening regression tests.
- metadata.setCredits remains the source of truth.

### Tooling / packages

- Python, Swift, Kotlin, and R consumer packages retain the stabilized analysis and interchange contracts.
- Release validation covers all public schemas, examples, package smoke tests, mapping registries, generated outputs, and release checksums.

### Compatibility

- The Free Exercise DB++ v1 exercise-definition core contract remains compatible.
- PLAN / ACTUAL / TARGET analysis stabilization is the main addition; independent schema versions remain unchanged.
- Garmin FIT, FHIR, HealthKit, Health Connect, IEEE/Open mHealth, taxonomy, and fine-anatomy exporters remain future work.
