# Current Project Status

Last updated: 2026-08-24

## Completed Phase

### Sprint 5 — PLAN vs ACTUAL

Implemented explicit PLAN-vs-ACTUAL matching and adherence analysis from the supplied roadmap.

Deliverables completed:

- Added `src/analysis/matching.py` with explicit-reference-first matching and no fuzzy matching by default.
- Added `src/analysis/plan_actual.py` with session, exercise, set, muscle, and movement-pattern adherence outputs.
- Implemented deterministic statuses: `matched`, `substitution`, `unplanned_addition`, `missing_prescription`, and `unable_to_match`.
- Added hand-calculated matching/adherence tests, documentation, and CI coverage.

Validation completed:

- Required matching statuses, missing prescriptions, substitution handling, set/repetition adherence, DB++ effective-set adherence, and movement-pattern adherence passed golden tests.
- Existing ACTUAL migration, PLAN, TARGET, coverage, PLAN-vs-PLAN, workout, release-contract, golden-mapping, medium-confidence policy, Python consumer, compilation, and diff checks passed.
- PLAN and ACTUAL source documents remain unmodified by analysis; standalone ACTUAL records remain valid.

Decisions and risks:

- Explicit prescription links take precedence; exact exercise-ID fallback is allowed only when unambiguous and not already consumed.
- Substitution status requires explicit substitution metadata; no silent equivalence or fuzzy name matching is inferred.
- Unlinked ACTUAL sessions are reported as `unable_to_match` rather than being guessed into a PLAN.

### Sprint 4 — ACTUAL schema 0.3 PLAN linkage

Implemented the compatible ACTUAL linkage layer from the supplied roadmap.

Deliverables completed:

- Extended `workout.schema.json` to accept ACTUAL `0.2.0` during transition and `0.3.0` with optional `planReference`, `exercisePrescriptionId`, `setPrescriptionId`, and `substitution` metadata.
- Added a linked ACTUAL example and migration tests covering standalone and PLAN-linked records.
- Added deterministic `0.1.x -> 0.2.0 -> 0.3.0` migration helpers in `src/workout/migrate_workout.py`; 0.2→0.3 preserves data and does not invent links.
- Updated ACTUAL documentation, README maturity wording, and CI migration validation.

Validation completed:

- ACTUAL schema fixtures, linked record validation, standalone 0.2 compatibility, migration behavior, and non-destructive checks passed.
- Existing PLAN, TARGET, analysis, workout, release-contract, golden-mapping, medium-confidence policy, Python consumer, compilation, and diff checks passed.
- PLAN and ACTUAL remain separate; no PLAN-vs-ACTUAL matching was added.

Decisions and risks:

- New PLAN-linked records should declare `schemaVersion: "0.3.0"`; legacy 0.2 records remain accepted while consumers transition.
- Substitutions are explicit metadata and do not infer or mutate the referenced PLAN.
- Migration is forward-only and preserves unknown fields/extensions.

### Sprint 3 — PLAN-vs-PLAN comparison

Implemented deterministic comparison of two PLAN revisions without introducing ACTUAL linkage.

Deliverables completed:

- Added `compare_plans(plan_a, plan_b, db)` in `src/analysis/plan_compare.py`.
- Compared direct, indirect, stabilizer participation, effective sets, movement patterns, session counts, and exercise-prescription frequencies.
- Preserved each plan’s native cycle and reported an explicit seven-day normalized comparison.
- Added deterministic JSON and tidy CSV writers.
- Added hand-calculated comparison tests and `docs/PLAN-COMPARISON.md`; CI runs the comparison tests.

Validation completed:

- PLAN-vs-PLAN golden calculations and deterministic JSON/CSV tests passed.
- Existing PLAN, TARGET, coverage, workout, release-contract, golden-mapping, medium-confidence policy, Python consumer, compilation, and diff checks passed.
- PLAN-vs-ACTUAL behavior, ACTUAL 0.2, PLAN 0.1, and the stable exercise DB contract remain unchanged.

Decisions and risks:

- Deltas are reported as `planB - planA`; native-cycle and normalized views are never conflated.
- Exercise frequencies use DB++ IDs when available and an explicit `custom:` key for custom prescriptions.
- CSV output is long-form and deterministic for research/review workflows; Parquet remains out of scope.

### Sprint 2 — Volume TARGET 0.1 + PLAN coverage analysis

Implemented the target contract and deterministic reference analysis from the supplied roadmap.

Deliverables completed:

- Added `volume-target.schema.json` version `0.1.0`, target examples, invalid fixtures, and `docs/VOLUME-TARGETS.md`.
- Added `src/analysis/coverage.py`, `src/analysis/plan_volume.py`, and `src/analysis/targets.py` with `analyze_plan(plan, db)` and `compare_to_targets(plan, target_profile, db)`.
- Preserved direct, indirect, stabilizer participation, effective-set, and movement-pattern outputs separately.
- Added native-cycle and explicit seven-day normalized views, coverage completeness, unmapped/ineligible diagnostics, and minimum/target/maximum gap states.
- Added hand-calculated analysis tests and CI validation/artifact coverage.

Validation completed:

- TARGET schema, examples, invalid fixtures, semantic range checks, and golden analysis calculations passed.
- Existing PLAN, workout, release-contract, golden-mapping, medium-confidence policy, Python consumer, compilation, and CLI checks passed.
- The stable exercise DB, ACTUAL 0.2 schema, and PLAN-vs-ACTUAL behavior remain unchanged.

Decisions and risks:

- Ranged PLAN set counts use target, then minimum, then maximum; this policy is recorded in analysis metadata.
- Custom/unknown exercises remain unmapped and receive no inferred muscle or movement-pattern roles.
- Known volume-ineligible exercises are mapped but reported separately; stabilizer participation is retained while effective credit remains `0.0`.

### Sprint 1 — Workout PLAN 0.1

Implemented the separate prescription contract from the supplied roadmap.

Deliverables completed:

- Added `workout-plan.schema.json` version `0.1.0` with immutable plan/revision identity, arbitrary native cycle lengths, planned sessions, stable prescription IDs, DB++ or custom exercise references, exact/ranged sets and reps, optional load and RPE/RIR, and notes.
- Added `src/plan/validate_plan.py` with Draft 2020-12 validation plus deterministic duplicate-ID and range-order checks.
- Added four valid examples under `examples/plans/`, four invalid fixtures under `fixtures/plan/invalid/`, and schema/example tests under `tests/plan/`.
- Added `docs/WORKOUT-PLAN.md`, README links, and CI validation.

Validation completed:

- All PLAN schema, example, invalid-fixture, semantic, and compile checks passed.
- Existing workout fixtures, release contract, golden mappings, medium-confidence policy, Python compilation, and Python consumer checks passed.
- ACTUAL `workout.schema.json` and the stable exercise DB contract were not modified.

Decisions and risks:

- PLAN stores prescriptions only; it does not duplicate DB++ muscle roles, effective-set totals, coverage totals, PLAN-vs-ACTUAL links, or external exporter fields.
- Native cycle length is preserved; seven-day normalization remains a future analysis concern and must be explicit.
- `planId` identifies the conceptual plan while `revisionId` identifies an immutable prescription revision.

### Phase 2H — R research integration package

Implemented and pushed in commit e078b1c; CI fixes pushed in commits 552b333 and 30e8ec7.

Deliverables completed:

- Added packages/r/fedbpp as a base-R-compatible research package using jsonlite for JSON I/O, with no tidyverse requirement.
- Added read-only database/workout loaders, schema validation, deterministic 0.1-to-0.2 migration access, observation data-frame helpers, and effective-set/longitudinal volume analysis.
- Preserved direct/indirect/stabilizer credit semantics as 1.0/0.5/0.0 and retained exercise IDs and annotation confidence; missing values remain explicit.
- Added reproducible examples, package metadata, tests, and CI setup.

Validation completed:

- R CI test task is wired through r-lib/actions/setup-r; local R/Rscript tooling is unavailable in this environment.
- Existing Kotlin, Swift, Python, mapping, workout, release-contract, golden-mapping, and medium-policy checks remain passing from prior phases.
- Commit pushed to origin/main.
- GitHub Actions run 32762590289 passed after correcting Kotlin and R fixture paths.

Decisions and risks:

- jsonlite is the sole required runtime dependency; tidyverse remains optional.
- Research tables are derived read-only views and retain source IDs, confidence, and missingness rather than mutating observations.
- JSON Schema remains the canonical cross-language validation contract; the base-R validator checks required interchange invariants.

### Phase 2G — Kotlin Android/Health Connect consumer package

Implemented and pushed in commit f8f06be (rebased onto remote bb7ed53).

Deliverables completed:

- Added packages/kotlin/fedbpp as a Kotlin 2.x/JVM-compatible consumer package using kotlinx.serialization.
- Added read-only Database/Workout loaders, validation, deterministic schema migration access, and effectiveSets with DB++ 1.0/0.5/0.0 credits.
- Added a platform-neutral Health Connect projection that preserves DB++ exercise IDs and reports extension-required/lossy fields explicitly.
- Added Kotlin tests, documentation, and CI coverage; generated build outputs remain ignored.

Validation completed:

- Kotlin Gradle test task is wired into CI; local Kotlin/Gradle tooling is unavailable in this environment.
- Existing Swift, Python, mapping, workout, release-contract, golden-mapping, and medium-policy checks remain passing from prior phases.
- Commit rebased and pushed to origin/main.

Decisions and risks:

- The package avoids a mandatory Android SDK dependency so JVM and Android callers can share the core models; apps map the projection to native Health Connect records.
- kotlinx.serialization uses ignoreUnknownKeys for forward-compatible DB++ decoding.
- Health Connect cannot represent every DB++ field; IDs, laterality, rep telemetry, and macro-segments remain namespaced extension data rather than inferred semantics.

### Phase 2F — Swift 6 consumer package

Implemented and pushed in commit 068dae7 (rebased onto remote 2243106).

Deliverables completed:

- Added packages/swift/FreeExerciseDBPlusPlus as a Swift 6 Foundation-only package.
- Added Codable and Sendable database/workout models, read-only lookup/search helpers, and effectiveSets(using:) with 1.0/0.5/0.0 credits.
- Added Swift package tests against the real 873-exercise database and an effective-set fixture.
- Added Swift CI coverage and excluded generated .build artifacts.

Validation completed:

- swift test passed on Swift 6.3.
- Existing Python, mapping, workout, release-contract, golden-mapping, and medium-policy checks remain passing from the prior phase.
- Commit rebased and pushed to origin/main.

Decisions and risks:

- Foundation-only APIs keep the package usable across macOS/iOS/watchOS targets.
- Unknown JSON fields are ignored by Codable to preserve forward compatibility; metadata uses a recursive JSON value type.
- Workout loading is schema-shaped Codable decoding; full JSON Schema validation remains the canonical cross-language contract.

### Phase 2E — Python consumer package

Implemented and pushed in commit f692092 (rebased onto remote e915c49).

Deliverables completed:

- Added packages/python/fedbpp with read-only Database and Exercise helpers.
- Added Workout loading, optional JSON Schema validation, deterministic migration access, and effective_sets analysis.
- Preserved DB++ direct/indirect/stabilizer credits as 1.0 / 0.5 / 0.0; incomplete sets and volume-ineligible exercises are excluded.
- Added package metadata, README usage examples, and CI coverage.
- Added tests against the real database and canonical workout fixtures.

Validation completed:

- Python package tests passed against 873 exercises.
- Mapping registry, Garmin, HealthKit, Health Connect, and workout fixture tests passed.
- Existing release-contract, golden-mapping, and medium-confidence tests passed.
- Python compile check and staged diff audit passed.
- Commit pushed to origin/main.

Decisions and risks:

- The package is dependency-light; jsonschema is optional and required only for Workout.validate/load validation.
- The package is read-only and does not mutate source JSON.
- Effective-set analysis is intentionally limited to stable DB++ semantics; it does not infer energy, body mass, or unsupported resistance effects.
- Package installation metadata targets Python 3.12+ and uses an optional validation extra.

## Planned Consumer Integrations

The plan includes Python, Swift 6, Kotlin for Android/Health Connect integration, and R for research integration; all four consumer phases are implemented. The roadmap is aligned to the completed sequence.

## Next Active Phase

All numbered roadmap sprints are complete through Sprint 9.

Completed in the final sprint sequence:

- Sprint 6: PLAN 0.2 phases, duration cycles, explicit plannedSets/setPrescriptionId, controlled progression metadata, optional/conditional prescriptions, migration, and phase-specific/time-varying coverage analysis.
- Sprint 7: deterministic tidy CSV exports for PLAN coverage and PLAN-vs-ACTUAL adherence.
- Sprint 8: source-artifact-aware interoperability registries and a documented FHIR PLAN mapping profile.
- Sprint 9: Python PLAN loading/analysis helpers and Swift PLAN Codable parity against the periodized fixture.

Final validation:

- Full workout, PLAN, TARGET, coverage, PLAN-vs-PLAN, PLAN-vs-ACTUAL, migration, export, release-contract, golden-mapping, medium-confidence, Python, Swift, compilation, and diff checks pass.
- Periodized PLAN analysis reports phase-specific effective sets and min/max/average summaries.
- Existing ACTUAL 0.2 compatibility, ACTUAL 0.3 linkage, PLAN 0.1 compatibility, and stable DB++ semantics remain intact.
- Kotlin and R consumer phases remain covered by the existing CI workflow; local Kotlin/R tooling is unavailable in this environment.

Ongoing work is maintenance, compatibility monitoring, CI review, and future taxonomy enrichment after real-world use. No further numbered sprint is pending.

## Working-tree note

CLAUDE.md, ROADMAP.md, and this handoff file remain untracked working-tree files by design. Do not stage or commit them unless explicitly requested.

## Next Session Override — Roadmap completeness remediation

This section supersedes the earlier statement that no numbered work remains. The latest audit found Sprints 1–5 and 7 substantially complete, with material gaps in Sprints 6, 8, and 9. Read `ROADMAP.md`, this file, and the repository, then implement the remediation below.

Preserve backward compatibility, PLAN/ACTUAL/TARGET/ANALYSIS separation, the DB++ `1.0/0.5/0.0` set-credit model, and explicit-reference-first matching. Do not add fuzzy matching.

### Required implementation

1. Fix PLAN 0.2 adherence in `src/analysis/plan_actual.py`: support both `sets`/`reps` and `plannedSets`; use `setPrescriptionId` when available; never crash when `sets` is absent; preserve missing, unplanned, incomplete, substituted, and unmatched sets. Add hand-calculated tests for heterogeneous planned sets, phase/session linkage, and substitutions.

2. Integrate `src/analysis/policies.py` into coverage and adherence so counting logic is not duplicated. Use target-then-min-then-max. Use `src/analysis/units.py` only for known compatible conversions; never guess unknown units.

3. Make `packages/python/fedbpp` standalone. Installed wheels must not import repository-level `src.*`. Expose `Plan`, `VolumeTarget`, `analyze_plan`, `compare_plans`, `compare_to_targets`, and `compare_plan_actual`. Build and install a wheel in an isolated temporary environment and test it outside the repository.

4. Complete practical Swift PLAN parity. Preserve load, effort, set type, laterality, notes, planned-set effort/notes, phases, progression, and optional/conditional prescriptions through Codable round trips. Test against the Python periodized fixture. Coverage must include direct, indirect, stabilizer participation, effective sets, movement patterns, native-cycle totals, explicit seven-day normalization, completeness, and phase-specific results. Do not claim unimplemented TARGET/comparison/adherence parity.

5. Replace nonexistent `Barbell_Bent_Over_Row` IDs in `examples/plans/eight-day-rotation.json` and `examples/plans/push-pull-legs.json` with a real DB++ ID. Add a test ensuring every PLAN example `exerciseId` resolves; custom `exerciseName` prescriptions remain valid.

6. Update `.github/workflows/build-db.yml` to run every Python consumer test, including `test_analysis.py`, plus the isolated wheel test. Ensure PLAN 0.2 adherence and PLAN-reference integrity tests run. Keep Swift/Kotlin/R checks.

7. Update `docs/WORKOUT-PLAN.md` for PLAN 0.1/0.2 and synchronize `docs/PLAN-ANALYSIS.md`, README, and consumer docs with actual APIs. Clearly distinguish declarative mappings, documented mappings, and executable exporters. Do not claim roadmap success criterion 14 is complete without a validated ACTUAL exporter; implementing an exporter is optional here.

### Required commands

```bash
PYTHONPATH=. bash -c 'for t in $(find tests -name "test_*.py" -type f | sort); do python3 "$t" free-exercise-db-plusplus.json || exit $?; done'
PYTHONPATH=packages/python:. bash -c 'for t in $(find packages/python/tests -name "test_*.py" -type f | sort); do python3 "$t" || exit $?; done'
python3 -m compileall -q src tests packages/python
swift test --package-path packages/swift/FreeExerciseDBPlusPlus
git diff --check
git status --short --branch
```

Also validate all schemas/fixtures, run the PLAN exercise-reference check, and build/install/test the Python wheel in an isolated temporary environment. Run Kotlin and R locally if available; otherwise verify CI coverage remains intact.

Before finishing, audit Sprints 1–9 again and report complete/partial/deferred with evidence. Do not commit or push unless explicitly requested.

### Existing untracked remediation files

Review and complete these rather than blindly replacing them:

- `docs/PLAN-ANALYSIS.md`
- `docs/adr/`
- `examples/plans/four-week-periodized.json`
- `examples/plans/push-pull-legs.json`
- `packages/python/fedbpp/analysis.py`
- `packages/python/tests/test_analysis.py`
- `packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/PlanAnalysis.swift`
- `packages/swift/FreeExerciseDBPlusPlus/Tests/FreeExerciseDBPlusPlusTests/PlanAnalysisTests.swift`
- `src/analysis/policies.py`
- `src/analysis/units.py`
- `tests/analysis/test_units_policies.py`

## Remediation completion — 2026-08-24

The roadmap completeness remediation is implemented and validated.

- PLAN 0.2 adherence now counts legacy `sets` and heterogeneous `plannedSets`, honors explicit `setPrescriptionId`, and retains missing, unplanned, incomplete, substituted, and unmatched work without fuzzy matching.
- Coverage and adherence share explicit counting policies; quantity conversion remains limited to known compatible units.
- The Python wheel is standalone, bundles schemas/reference logic, has no `src.*` imports, and exposes `Plan`, `VolumeTarget`, `analyze_plan`, `compare_plans`, `compare_to_targets`, and `compare_plan_actual`.
- Swift PLAN Codable round trips preserve PLAN 0.2 fields and coverage includes native/normalized, completeness, muscle-role, movement-pattern, and phase-specific results.
- All PLAN example DB++ references resolve. CI discovers every Python consumer test and performs an isolated wheel import check while retaining Swift/Kotlin/R coverage.
- Documentation now distinguishes declarative registries, documented mapping profiles, and executable exporters. No validated ACTUAL exporter exists, so roadmap success criterion 14 remains partial.

Sprint audit:

- Sprints 1–9: complete against their stated sprint deliverables.
- Overall definition-of-success criteria 1–13: complete.
- Overall criterion 14: partial; a documented FHIR PLAN mapping exists, but a validated ACTUAL exporter remains deferred/optional.
- Taxonomy enrichment and a validated ACTUAL exporter: deferred future work.

Validation completed:

- All 35 zero-argument repository Python tests executed successfully, plus legacy direct-script checks.
- All 6 Python consumer tests executed successfully.
- Final standalone wheel built and imported from an isolated `/tmp` installation with site-packages disabled.
- Swift tests passed (4 tests); workflow YAML, Python compilation, and `git diff --check` passed.
- Gradle and Rscript are unavailable locally; Kotlin and R test jobs remain present in CI.

No commit or push was performed.

Deep completion audit follow-up:

- Executed every required API from the installed wheel, not only import checks.
- Corrected setuptools discovery so wheels contain only `fedbpp*` packages and bundled schemas; generated `build/`, tests, bytecode, and nested package copies are excluded.
- Inspected the final wheel manifest and removed local generated build artifacts after validation.
