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

## 1.15.4 - 2026-08-30

- Add public Swift `goalPolicy(_:)` accessors at the package and
  `TrainingEngine` levels, returning immutable released goal-policy documents
  and `nil` for unknown identifiers.
- Add Swift coverage for all three released goal-policy identifiers and the
  endurance policy's 15--18--20 repetition / RIR 2 defaults.
- Preserve all exercise data, evidence, schemas, resolver behavior, and shared
  cross-language fixtures unchanged.

## 1.15.3 - 2026-08-30

- Contract-hardening patch: identify WorkoutIntent and TrainingProfile as
  schema `0.2.0` after expanding the released goal vocabulary; runtime
  consumers continue accepting historical `0.1.0` documents.
- Add the canonical full endurance generation fixture and verify Python,
  Swift, Kotlin/JVM, and R generation parity, including attached evaluation.
- Preserve the v1.15.2 endurance policy and its 15--18--20 / RIR 2 defaults;
  keep the immutable upstream release snapshot pinned.
- No LLM, network, reticulate, Python-subprocess, or other external semantic
  engine dependency was added.

## 1.15.2 - 2026-08-30

- Add the evidence-backed `general-endurance-v1` goal policy with conservative
  15--18--20 repetition, RIR 2, and coverage defaults.
- Add evidence blocks to all three goal policies and embed the loading
  continuum and repetitions-in-reserve references in the generated database.
- Recognize `endurance` consistently across Python, Swift, Kotlin, and R
  resolvers with cross-language parity coverage.
- Bump `converterVersion` to 0.8.1; the exercise-data schema and exercise IDs
  remain unchanged.

## 1.15.1 - 2026-08-28

- Add runnable external-consumer history, TrainingState, progression, and
  adaptation examples for Swift, Kotlin/JVM, Python, and R.
- Replace Swift integration placeholders with real public Codable
  decode/encode examples and direct links to the executable SPM consumer.
- Execute the Swift and Kotlin history/adaptation consumers in CI and record
  the consumer hardening audit.
- Preserve v1.15.0 application-contract and training methodology semantics.

## 1.15.0 - 2026-08-28

- Add a versioned, transport-neutral TrainingRequest/TrainingResult contract
  with explicit resolve, generation, evaluation, state, progression, and
  adaptation operations.
- Expose the contract through typed Swift and Kotlin facades, Python dict and
  typed helpers, and an offline base-R named-list facade while preserving all
  existing lower-level engine APIs.
- Add bundled schemas, executable four-language consumers, canonical
  application fixtures, full-envelope parity checks, integration guides, and
  CI coverage for the application boundary.
- Preserve deterministic training semantics; no new training methodology,
  LLM, network, or current-time dependency is introduced.

## 1.14.1 - 2026-08-28

- Enforce full Python-authored R parity checks for intent, evaluation, history,
  progression, generation, and adaptation, including canonical generation
  result provenance and selection ordering.

## 1.14.0 - 2026-08-28

- Complete the native R research/analysis engine for the released DB++ training
  semantics, including intent resolution, PLAN/TARGET evaluation,
  TrainingHistory, TrainingState, progression, generation, and adaptation.
- Bundle canonical database, relationships, and intent-policy resources for
  installed-package workflows.
- Add base-R research data.frame views, provenance helpers, JSON shape-safe
  serialization, and R API/release audit documentation.
- Keep the package independent of Python, reticulate, Java, tidyverse, network
  services, and LLM APIs.

## 1.13.0 - 2026-08-28

- Complete the native Kotlin/JVM training engine port with the offline
  `TrainingEngine` facade for intent resolution, production generation,
  evaluation, history/state derivation, progression, and adaptive coaching.
- Bundle canonical database and relationship resources for plain JVM and
  Android-compatible consumers without an Android framework dependency.
- Add Python-authored Kotlin parity fixtures, serialization round-trip checks,
  an external Gradle consumer, resource integrity checks, and Kotlin API docs.
- Keep the R full research/analysis engine port scheduled for v1.14.

## 1.12.0 - 2026-08-27

- Make the completed Swift engine a production-ready, Foundation-only Swift
  Package Manager dependency with a single `TrainingEngine` facade.
- Add strongly typed intent, PLAN, ACTUAL, TARGET, profile, history, state,
  evaluation, generation, progression, and adaptive-coaching contracts with
  stable Codable round trips and machine-readable outcomes.
- Bundle offline resources, validate canonical resource copies in CI, and add
  an external SPM consumer plus performance smoke coverage.
- Preserve deterministic v1.11 engine semantics; this release adds no new
  training algorithm milestone. Kotlin remains v1.13 and R remains v1.14.

## 1.11.1 - 2026-08-27

- Correct the native Swift history, progression, generation, intent, and
  adaptive-coaching outputs to the Python reference semantics.
- Expand deterministic cross-language fixtures and add exact external Swift
  consumer and installed-wheel acceptance checks.
- Refresh release checksums for the canonical database and relationship
  artifacts; the immutable v1.11.0 tag is unchanged.

## 1.11.0 - 2026-08-26

- Complete the Python reference audit and full native Swift engine parity for
  intent, TARGET/profile handling, evaluation, history/state, progression,
  production generation, and adaptive coaching.
- Add deterministic Python-authored evaluation, history, progression,
  generation, and adaptation fixtures with an external Swift SPM consumer.
- Keep the release offline with no Python bridge, network dependency, or LLM;
  defer the full Kotlin port to v1.13 and the full R port to v1.14.
- Define v1.12 as Swift SPM packaging and app-readiness hardening, with no
  unfinished core Swift engine semantics.

## 1.10.1 - 2026-08-26

- Stabilize `IntentResolutionResult.explicitOverrides` as a fixed typed object across all statuses.
- Extend canonical TARGET relational validation to frequency, movement-pattern, and family ranges, including fallback validation.

## 1.10.0 - 2026-08-26

- Add structured WorkoutIntent resolution, versioned goal/environment policies, and intent CLI commands.
- Add hard per-session exercise-count constraints to canonical evaluation and generation.

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


## 1.9.0 - 2026-08-26

- Added deterministic, advisory adaptive coaching through `adapt_plan()` and the versioned `general-adaptive-v1` CoachingPolicy.
- Added evaluator-gated immutable PLAN revision/regeneration proposals, machine-readable changes, decisions, and provenance; no proposal is activated automatically.
- Added `fedbpp adapt-plan` and adaptive-coaching guidance.
- Hardened substitution evidence so it is derived solely from the canonical
  TrainingState as-of/window/timezone boundary, including compact windowed
  replacement provenance.
- Hardened evaluator gating so a revision or regeneration cannot worsen the
  magnitude of any canonical TARGET maximum excess.
