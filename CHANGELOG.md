## 1.2.0 - 2026-08-25

- Added authoritative interoperability audits and compatibility matrix for FIT, Health Connect, HealthKit, FHIR Physical Activity, IEEE 1752.1/Open mHealth, and legacy Google Fit.
- Added structural mapping metadata, exercise identity crosswalk and loss-report schemas.
- Added reviewed Garmin FIT exercise identity crosswalk, Health Connect category compatibility metadata, deterministic coverage reports, type-aware validation/registry modules, loss fixtures, and packaged Python lookup API.
- Import/export serializers remain v1.3 work.

## 1.3.0 - 2026-08-25

- Added a strict-by-default conversion API with deterministic results, provenance, normalization, and machine-readable loss reporting.
- Added operational FHIR R4 Physical Activity Bundle import/export using the reviewed mapping registry and exact identity crosswalk.
- Added custom/unknown exercise preservation and explicit ambiguous/unmapped identity failures.
- Added the `fedbpp` CLI for validation, PLAN/ACTUAL/TARGET analysis, mapping lookup, and import/export.
- Added packaged conversion examples, fixtures, documentation, and wheel console-script support.
- Garmin FIT binary, Health Connect file, and HealthKit file support remain intentionally bounded by licensing and platform API constraints.

# Changelog

## 1.8.0 - 2026-08-25

- Added deterministic Python PLAN proposal generation with the versioned
  `full-body-general-v1` and `upper-lower-general-v1` reference PlanningPolicies.
- Added canonical-evaluator-gated generation reports, explicit hard
  unsatisfiability/target-gap reasons, deterministic IDs and provenance,
  optional current-plan and TrainingState continuity, and `fedbpp generate-plan`.
- Added plan-generation policy and determinism ADRs and public guidance.
- Existing PLAN, ACTUAL, TARGET, TrainingProfile, TrainingState, relationship,
  and evaluation schemas remain unchanged.

## 1.7.1 - 2026-08-25

- Corrected the direction-specific RPE/RIR effort reason codes without changing
  double-progression hold or success semantics.
- Populated TrainingState exercise prescription adherence from canonical
  longitudinal exercise rows, preserving missingness and prescription identity.
- Added deterministic per-prescription skip and substitution counts.
- Clarified latest-performance compatibility fields and added deterministic
  `latestPerformance` / `recentPerformances` structures.
- Made policy-map progression evaluation direct and per-prescription while
  preserving PLAN order and advisory, non-mutating behavior.

No PLAN, ACTUAL, TARGET, or independent schema versions changed.

## 1.7.0 - 2026-08-25

- Added deterministic derived `TrainingState` with explicit as-of timestamps,
  windows, active PLAN context, exercise/family/muscle/adherence state, and
  provenance.
- Added versioned advisory `hold-v1` and `double-progression-v1` policies,
  machine-readable `CoachDecision`, load increment validation, and evidence.
- Added `fedbpp training-state` and `fedbpp progress`; PLAN generation,
  mutation, and automatic revision remain out of scope.

## 1.6.0 - 2026-08-25

- Added portable TrainingProfile schema and DB-aware profile validation.
- Added deterministic Python PlanEvaluation with target, frequency,
  movement-pattern, family, equipment, availability, completeness, and
  provenance sections.
- Added `fedbpp validate profile` and `fedbpp evaluate-plan` plus examples,
  ADRs, and a golden evaluator fixture.
- Release assets include the TrainingProfile schema and PlanEvaluation guides.
- TARGET remains backward compatible; plan generation and coaching remain out
  of scope.

## 1.5.1 - 2026-08-25

- Fixed relationship coverage comparison to use authoritative
  `metadata.setCredits` through the canonical analysis policy.
- Removed the silent hard-coded effective-set-credit fallback.
- No exercise-family memberships, relationship schema, or other public
  analysis semantics changed.

## 1.5.0 - 2026-08-25

- Added the optional, independently versioned exercise-family and relationship
  artifact with curated deterministic assignments, variation dimensions,
  provenance, validation, and coverage reports.
- Added `RelationshipRegistry`, family-level PLAN comparison helpers,
  descriptive PLAN/ACTUAL relationship context, exercise coverage comparison,
  and `fedbpp family`, `family-members`, `related`, and `compare-exercises`
  commands.
- Family membership remains taxonomic/descriptive; no equivalence or automatic
  substitution semantics were added.

## 1.4.1 - 2026-08-25

- Fixed longitudinal repeated-occurrence matching, revision-boundary clipping,
  missed-set ranges, canonical exercise adherence, substitution reasons,
  unplanned coverage, exposure frequency, target transitions, and period semantics.
- Added longitudinal regression, cohort, wheel, and CLI coverage.

## 1.4.0 - 2026-08-25

- Added longitudinal PLAN-vs-ACTUAL analysis across calendar, rolling, native
  cycle, phase, and custom periods.
- Added plan revision activation/linkage, missed and unplanned session reports,
  target aggregation, substitutions, exposure frequency, coverage completeness,
  and explicit missing-data states.
- Added deterministic subject-period-muscle, subject-session, and
  subject-session-exercise CSV exports plus descriptive cohort support.
- Added the public `fedbpp.longitudinal` API and `fedbpp analyze-history` /
  `fedbpp research-export` commands.
- No inferential statistics, recommendations, physiological equivalence claims,
  or exercise-family graph are included.

## 1.3.1 - 2026-08-25

- Fixed conversion validation so strict and lossy conversion validation works
  when the optional `jsonschema` dependency is not installed.
- No v1.4 features are included in this patch release.

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


## 1.9.0 - 2026-08-25

- Added deterministic, advisory adaptive coaching through `adapt_plan()` and the versioned `general-adaptive-v1` CoachingPolicy.
- Added evaluator-gated immutable PLAN revision/regeneration proposals, machine-readable changes, decisions, and provenance; no proposal is activated automatically.
- Added `fedbpp adapt-plan` and adaptive-coaching guidance.
