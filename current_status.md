# Current status — v1.11 engine work

## Revised release scope

The current v1.11 release focuses on **Swift native core-engine parity with
the Python reference**. Do not expand this release to complete Kotlin or R
ports.

- Swift is the only native implementation that must reach the complete
  v1.11 engine scope: WorkoutIntent resolution, PLAN evaluation, canonical
  generation, full TrainingHistory/TrainingState, progression, CoachDecision,
  and adaptive planning.
- Kotlin work is deferred to a future release. Preserve the current native
  Kotlin improvements, but do not claim full Kotlin engine parity or block the
  Swift-focused v1.11 release on Kotlin generation/state/adaptation parity.
- R work is deferred to a future release. Do not claim full R engine parity or
  block the Swift-focused v1.11 release on R generation/state/adaptation.
- Python remains the executable semantic oracle. Do not redesign its behavior
  while porting Swift.

Future-release ownership:

- Kotlin: complete production generator, full adherence-rich state,
  progression, adaptive coaching, fixtures, consumer coverage, and exact
  Python parity.
- R: complete required research/analysis semantics, artifact handling, and any
  later native planning/adaptation decision.

## Execution protocol for HANDOFF.md

Implement `HANDOFF.md` one part at a time, in its stated order. For every
part:

1. Read the relevant Python oracle, schemas, ADRs/docs, and tests before
   changing code.
2. Implement only that part's in-scope work. Do not begin the next part in
   the same work cycle.
3. Double-check the implementation with focused tests and the applicable
   cross-language/golden comparisons. Run the required language and repository
   checks; record any limitation explicitly.
4. Commit the completed and verified part as its own commit.
5. Update this file with what changed, verification evidence, the commit, and
   precise instructions for resuming the next part.
6. Pause for human review and provide a concise BLUF. Do not continue to the
   next part until the user explicitly resumes the work.

The current cycle has completed **Part A — First Audit Python for
Completeness**. The Python engine is the semantic oracle for the remaining
native work; no Python rewrite was required.

## Phase tracker

- Part A — Python completeness audit: **complete; audited below**
- Part B — Python golden fixtures: **complete; audited below**
- Part C — canonical comparison rules: **complete; audited below**
- Part D — Swift engine architecture: **complete; audited below**
- Part E — Swift TrainingEngine façade: **complete; audited below**
- Part F — Swift typed core domain models: **complete; audited below**
- Part G — Swift database/relationship resource loading: **complete; audited below**
- Part H — Swift full PLAN analysis: **complete; audited below**
- Part I — Swift full PLAN evaluation: **complete; audited below**
- Part J — Swift TARGET validation and merging: **complete; audited below**
- Part K — Swift TrainingHistory model and semantics: **complete; audited below**
- Part L — Swift offset-aware time: **complete; audited below**
- Part M — Swift full TrainingState envelope: **complete; audited below**
- Part N — Swift TrainingState windows: **complete; audited below**
- Part O — Swift active-plan resolution: **complete; audited below**
- Part P — Swift exercise state: **complete; audited below**
- Part Q — Swift adherence-rich state: **complete; audited below**
- Part R — Swift missingness semantics: **complete; audited below**
- Part S — Swift family state: **complete; audited below**

### Resume instructions for the next phase

Begin Part L by adding offset-aware timestamp parsing and comparison helpers
for history semantics. Keep Part M state derivation and broader time-window
behavior out of that cycle; preserve the Python oracle and do not work on
Kotlin or R.

## Part B fixture evidence

Added Python-authored, reproducible fixtures under
`fixtures/cross-language/{evaluation,history,progression,generation,adaptation}`.
The authoring tool is `tools/generate_cross_language_engine_fixtures.py`; it
loads the repository database and relationship artifact, invokes the Python
oracle, and writes deterministic JSON inputs, expected outputs, and metadata.

Coverage includes evaluation constraints/target gaps/incomplete coverage and
provenance; active-plan history windows, timezone/as-of handling, and ACTUAL
matching; progression success, hold, incomplete-workout, and effort-boundary
decisions; evaluator-gated generation with required exercise selection; and
adaptive revision proposals with progression decisions. The generation case
is `generated`; the adaptation case is `revision_proposed`; the evaluation
case deliberately records `hard_constraint_violation` so native consumers
must preserve failure semantics.

Verification: rerunning the authoring tool reproduced the committed artifacts;
all five expected JSON documents loaded successfully and reported the statuses
above. Python package tests could not be rerun in this environment because
neither `pytest` nor the `pytest` Python module is installed. No Swift, Kotlin,
or R source was changed.

Part B commit: `62c0334` (`test: add Python engine parity fixtures`).

## Part C comparison-rule evidence

Defined one strict Python↔native comparison policy in
`docs/CROSS-LANGUAGE-ENGINE-PARITY.md` and implemented its reference checker
as `tools/compare_canonical_json.py`. Only JSON object member order,
whitespace, and mathematically equal integer/float representations are
ignored. Arrays, null-versus-missing fields, ordering, counts, policy
identity, statuses, reason codes, provenance, coverage, and decision contents
remain semantic.

Verification: the checker passed self-comparison of a canonical expected
fixture, numeric-equivalence coverage, null/missing rejection, array-order
rejection, Python syntax compilation, and `git diff --check`. No engine
implementation was changed in Part C.

Part C commit: pending commit after review.

## Part D architecture evidence

Recorded the native Swift package boundary and implementation constraints in
`docs/adr/0027-swift-native-engine-architecture.md`. The existing
`packages/swift/FreeExerciseDBPlusPlus` package remains the sole Swift package,
uses Swift 6 and Foundation, keeps portable values Codable/Sendable where
practical, and has no UI, network, subprocess, Python, or LLM dependency.
Part D made no semantic engine changes and intentionally leaves typed public
engine expansion to Parts E–F.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 12 tests. A source audit found only Foundation imports and no
prohibited runtime dependencies.

Part D commit: pending commit after review.

## Part E façade evidence

Extended the existing native `TrainingEngine` façade with the application-level
`generatePlanFromIntent` entry point, alongside its existing intent validation,
resolution, evaluation, and TrainingState projection methods. The façade keeps
database and relationship dependencies injected as immutable values and
delegates to the native implementations, preserving the shared JSON result
shape during the typed-domain migration. Full typed domain results and the
remaining generation/progression/adaptation entry points are intentionally
reserved for Parts F and later.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 13 tests, including a façade draft-generation regression. No
Kotlin or R functionality was changed.

Part E commit: pending commit after review.

## Part F typed-domain evidence

Added Codable/Sendable value models for `TargetRange`, `VolumeTarget`,
`TrainingProfile`, availability, `TrainingHistory`, plan activations, history
windows, exercise/training state, `CoachDecision`, and generated/adaptive
result envelopes. Extended ACTUAL values with optional plan linkage,
prescription linkage, substitution, set prescription, and effort telemetry.
`JSONValue` remains limited to open-ended metadata and detailed forward-
compatible result sections; the primary portable identities and containers are
typed.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 14 tests, including canonical TARGET/profile/PLAN decoding and a
typed `TrainingHistory` Codable round trip. `git diff --check` passed. No
Python, Kotlin, or R source was changed.

Part F commit: pending commit after review.

## Part G resource-loading evidence

Packaged the canonical `free-exercise-db-plusplus.json`,
`exercise-relationships.json`, PLAN/WORKOUT/profile/TARGET/CoachDecision
schemas, and existing intent policy resources in the Swift target resources.
Added `TrainingEngine.bundled()` to load the database and relationship
artifact through `Bundle.module`; custom database/relationship injection
remains available through the existing initializer. Database metadata and
relationship schema versions remain exposed on the loaded values.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 15 tests, including bundled resource loading and canonical family
lookup. `git diff --check` passed. No Python, Kotlin, or R source was changed.

Part G commit: pending commit after review.

## Part H analysis evidence

Expanded Swift `WorkoutPlan.coverage(using:)` to preserve independent set
ranges and representative scalar views for direct, indirect, stabilizer,
effective, and movement-pattern volume. The implementation now honors counted
and excluded set types, database-configured set credits, volume eligibility,
unmapped/ineligible completeness ranges and prescription IDs, native and
normalized seven-day periods, phase-specific views, exposure frequency, and
analysis provenance.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 15 tests, including database set-credit, arbitrary-cycle
normalization, range, and completeness assertions. `git diff --check` passed.
No Python, Kotlin, or R source was changed.

Part H commit: pending commit after review.

## Part I evaluation evidence

Completed the Swift evaluator parity surface for summary status, target gaps,
muscle/frequency/pattern/family comparisons, equipment and profile findings,
availability, exercise counts, completeness, warnings, and provenance. Family
coverage now preserves canonical membership, exposures, planned ranges, and
variant dimensions; unknown exercises and unique preference summaries follow
the Python oracle.

Verification: the new Swift golden test compares the complete evaluation
document against `fixtures/cross-language/evaluation/expected.json` and passes
exactly under the Part C comparison policy. The full
`swift test --package-path packages/swift/FreeExerciseDBPlusPlus` suite passes
all 16 tests, and `git diff --check` passes. No Python, Kotlin, or R source was
changed.

Part I commit: pending commit after review.

## Part J target evidence

Exposed Swift `TrainingEngine` methods for TARGET validation and
field-preserving explicit TARGET merging. Partial `min`/`target`/`max` ranges
and nested frequency muscle ranges retain unrelated base members; validation
returns stable path-qualified range conflicts, which intent resolution maps to
`TARGET_OVERRIDE_CONFLICT`.

Verification: the façade regression covers partial-range preservation and an
invalid target range. The complete
`swift test --package-path packages/swift/FreeExerciseDBPlusPlus` suite passes
all 17 tests, including the Python golden PLAN evaluation, and
`git diff --check` passes. No Python, Kotlin, or R source was changed.

Part J commit: pending commit after review.

## Part K history evidence

Completed the typed Swift `TrainingHistory` representation for subject
identity, PLAN revisions, plan activations, and ACTUAL workouts. ACTUAL
observations preserve session and plan references, prescription IDs,
set-level prescription IDs and telemetry fields, and typed substitution
references. An observation without a prescription or substitution is exposed
as unplanned work. History decoding defaults omitted optional collections to
empty, matching the canonical history fixture shape; plan lookup and
activation filtering helpers are available without resolving active revisions
or applying time windows.

Added a date-string-based `ScheduledOccurrence` value for the later scheduling
surface. It intentionally does not parse or compare offsets; that behavior is
reserved for Part L.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 19 tests, including canonical history linkage and plan-linked
substitution/unplanned-work regressions. `git diff --check` passed. No Python,
Kotlin, or R source was changed.

Part K commit: `6494743` (`feat: complete Swift training history domain`).

## Part L time evidence

Added a shared offset-aware ISO-8601 parser that rejects naive timestamps,
accepts fractional and non-fractional instants, returns absolute `Date`
chronology, and retains the numeric source offset for local calendar-boundary
construction. Updated the existing Swift history projection to use this
parser for `asOf`, activation bounds, and ACTUAL future exclusion. Rolling
window dates are now derived in the as-of offset, while instant comparisons
remain absolute across differing offsets and DST-adjacent transitions.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 21 tests, including UTC, `-05:00`, `-04:00`, same-calendar-date
future exclusion, naive-timestamp rejection, and DST-adjacent boundary
regressions. `git diff --check` passed. No Python, Kotlin, or R source was
changed.

Part L commit: `b9829a0` (`feat: add Swift offset-aware time semantics`).

## Part M state evidence

Completed the typed `TrainingState` envelope and added a typed
`TrainingEngine.deriveTrainingState` overload. The state now consistently
represents `stateVersion`, `subjectId`, `asOf`, `historyWindow`, `activePlan`,
`exerciseState`, `familyState`, `muscleState`, `adherenceState`, `sessionState`,
and `provenance`, with Codable defaults for optional/empty sections. The
existing JSON projection now emits `sessionState` on valid results and records
the as-of numeric offset in provenance. Detailed exercise-state, adherence,
active-plan-resolution, and alternate-window semantics remain assigned to
Parts N/Q/O/P as specified by `HANDOFF.md`.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 22 tests, including typed state-envelope decoding and invalid
as-of handling. `git diff --check` passed. No Python, Kotlin, or R source was
changed.

Part M commit: `3f55dd8` (`feat: add typed Swift training state envelope`).

## Part N window evidence

Added exact Python-aligned window selection to the Swift state projection and
`TrainingEngine` façade: `last_7_days`, `last_28_days`,
`current_plan_cycle`, `current_phase`, and custom date ranges. Window ends are
clamped to the supplied `asOf` calendar date, ACTUAL filtering remains
offset-aware and future-exclusive, and cycle/phase boundaries use the active
activation anchor and plan durations. The existing two-argument API retains
the `last_28_days` default.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 24 tests, including last-seven-day, custom-range, current-cycle,
and current-phase boundary regressions. `git diff --check` passed. No Python,
Kotlin, or R source was changed.

Part N commit: `01341fa` (`feat: add Swift training state windows`).

## Part O active-plan evidence

Added typed `TrainingEngine` resolution for the uniquely active PLAN revision
at an offset-aware `asOf`. Selection is independent of input ordering, honors
activation start/end intervals, rejects overlapping active windows, and
returns no plan when no unambiguous context exists. Workout resolution
honors an explicit plan/revision reference first; the JSON state path now
applies the same no-arbitrary-overlap rule and uses a uniquely referenced
historical plan when activation metadata is absent.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 26 tests, including order-independent revision selection, future
and ended activations, explicit workout references, no-active-plan behavior,
and overlapping-activation rejection. `git diff --check` passed. No Python,
Kotlin, or R source was changed.

Part O commit: `1895418` (`feat: add Swift active plan resolution`).

## Part P exercise-state evidence

Expanded Swift `exerciseState` to preserve the Python-facing performance
fields: latest and recent performance records, last prescription/actual,
recent session and counted-set totals, reps, loads, RPE, RIR, and set-type
histories, plus substitution and unplanned counts. Completed-set extraction
uses the canonical counted set types and excludes incomplete/non-counted sets;
prescription adherence remains reserved for Part Q.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 27 tests, including the canonical history performance-field
regression. `git diff --check` passed. No Python, Kotlin, or R source was
changed.

Part P commit: `dcd013f` (`feat: expand Swift exercise state`).

## Part Q adherence evidence

Added Python-shaped adherence state to the Swift projection. It now emits
session and exercise-prescription rows with matched, substitution, missing,
and unplanned classifications; canonical counted-set totals; set-count
adherence; comparable reps/load/RPE/RIR adherence when planned and actual
telemetry is present; missed-session and unplanned collections; repeated skip
and substitution counts; and substitution history grouped by prescription.
Missing telemetry remains explicitly non-comparable rather than being
converted to zero.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 27 tests, including canonical matched adherence and unplanned/
substitution regressions. `git diff --check` passed. No Python, Kotlin, or R
source was changed.

Part Q commit: `a7f564f` (`feat: add Swift adherence state`).

## Part R missingness evidence

Added the typed `MissingnessState` vocabulary and preserved missingness at the
adherence-row boundary. Planned-but-unrecorded prescriptions are marked
`not_recorded`; unplanned additions are `not_prescribed`; missing exercise
identity is `unknown`; and explicit references outside the linked session are
`unable_to_match`. These states remain distinct from numeric zero and from
each other, while the existing plan-analysis paths continue to report
`unmapped` and `volume_ineligible` coverage separately.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 28 tests, including distinct missingness regressions for recorded,
unplanned, and unable-to-match actuals. `git diff --check` passed. No Python,
Kotlin, or R source was changed.

Part R commit: `c443364` (`feat: preserve Swift missingness states`).

## Part S family-state evidence

Added relationship-backed `familyState` derivation to the Swift state
projection. Family rows preserve deterministic recent exercise IDs, the most
recent exercise, and explicit substitution totals. Family membership alone is
never treated as a substitution; only actual observations carrying an
explicit substitution record contribute to substitution counts.

Verification: `swift test --package-path packages/swift/FreeExerciseDBPlusPlus`
passed all 29 tests, including a same-family membership regression proving
that substitution is not inferred. `git diff --check` passed. No Python,
Kotlin, or R source was changed.

Part S commit: `39b348b` (`feat: add Swift family state`).

## Part A audit evidence

Audited the Python modules listed in `HANDOFF.md`, their public exports in
`packages/python/fedbpp/__init__.py`, the shipped schemas, the v1.1–v1.10.1
release documentation/ADRs, and the associated package, analysis, plan,
relationship, target, training, workout, longitudinal, and interop tests.

The fourteen required behaviors are present and coherent:

1. PLAN validation — schema and semantic invalid-fixture tests pass.
2. ACTUAL validation — schema, migration, and invalid-fixture tests pass.
3. TARGET validation — schema and relational-range tests pass.
4. TrainingProfile — schema, contradiction, and DB/relationship validation tests pass.
5. Relationships — artifact validation, golden families, coverage, and substitution enrichment tests pass.
6. PlanEvaluation — deterministic evaluation, profile findings, target gaps, provenance, and incompleteness tests pass.
7. TrainingHistory — period, revision, activation, date-window, timezone, and CSV/cohort tests pass.
8. TrainingState — bounded windows, adherence, matching, substitutions, skip counts, and provenance tests pass.
9. Progression — double-progression, effort direction, hold, regression, and policy-map tests pass.
10. CoachDecision — deterministic explainable decisions, schema validation, and immutable proposal tests pass.
11. Production PlanGeneration — deterministic candidate selection, constraints, frequency/pattern/family targets, locked exercises, and evaluator gating tests pass.
12. Adaptive coaching — progression, substitution, regeneration, target-maximum gating, and equipment drift tests pass.
13. WorkoutIntent resolution — validation, precedence, policies, partial ranges, weekdays, conflicts, and provenance tests pass.
14. `generate_plan_from_intent` — deterministic flagship generation, evaluation gating, and history-aware intent tests pass.

Verification: the three `packages/python/tests/test_*.py` package checks pass;
the focused Python suites pass (`123 passed` across analysis, plan,
relationships, target, training, workout, longitudinal, and interop); and the
three database-argument contract checks pass. The unqualified `pytest -q`
command is not valid for this repository because several contract tests
consume `sys.argv[1]` as the database path; the documented per-suite commands
were used instead.

No genuine Python defect was found, so no Python source or regression test was
changed in Part A.

### Exact Part B fixture gaps

`fixtures/cross-language/intent/` already contains resolution and flagship
intent-generation fixtures. These required families do not exist yet:

- `evaluation/`: PlanEvaluation constraints, target gaps, incomplete coverage, relationships, and provenance.
- `history/`: active revisions, windows, timezone/as-of handling, ACTUAL matching, adherence, substitutions, and arbitrary cycles.
- `progression/`: effort classifications, progression/hold/regression, and policy-map decisions.
- `generation/`: direct planning policies, locked/required exercises and families, target allocation, and unsatisfiable constraints.
- `adaptation/`: adaptive progression, substitutions, regeneration, target-maximum, and evaluator gates.

## Repository state

- Branch: `main`
- Current committed HEAD before the next implementation phase: `39b348b`
  (`feat: add Swift family state`)
- The older `564272a release: prepare v1.11.0` commit is superseded. **Do not
  tag or release it.**
- No `v1.11.0` tag has been created.
- `HANDOFF.md` is currently untracked and is user-provided. Preserve it.
- Before each implementation phase, inspect `git status` and preserve unrelated
  user changes; do not discard them.

## Work completed in the working tree

- Swift:
  - native `evaluatePlan(...)` foundation with coverage, target, equipment,
    availability, constraint, completeness, warnings, and provenance output;
  - custom set-credit evaluator regression;
  - offset-aware same-day future-workout exclusion regression;
  - `TrainingEngine` façade for validation, intent resolution, evaluation, and
    current TrainingState derivation.
- Kotlin (deferred future work; retain but do not extend for this release):
  - evaluator foundation and evaluator-gated generator foundation;
  - candidate, day-offset, session-count, contribution, frequency, pattern,
    family, target, and session-minimum primitives;
  - timestamp fixes and regressions.

## Verified commands

- `swift test --package-path packages/swift/FreeExerciseDBPlusPlus` passed
  before the latest Kotlin-only generator edits.
- `gradle --no-daemon test --project-dir packages/kotlin/fedbpp` passed after
  the latest Kotlin changes.

Run Swift tests again after every Swift change. Do not infer full parity from
language-local tests; add Python-authored golden fixtures and compare normalized
results field-by-field.

## Immediate next task: Part A Python completeness audit

After Part A is completed and reviewed, continue incrementally using the
Python reference as the oracle. The later Swift port uses these files:

- `packages/python/fedbpp/planning.py`
- `packages/python/fedbpp/plan_evaluation.py`
- `packages/python/fedbpp/training_state.py`
- `packages/python/fedbpp/progression.py`
- `packages/python/fedbpp/coaching.py`
- `packages/python/fedbpp/intent.py`

Priority order:

1. Finish Swift evaluator parity against shared fixtures.
2. Replace Swift's lightweight `generatePlanFromIntent` constructor with the
   evaluator-gated Python planning algorithm.
3. Port complete TrainingHistory/TrainingState semantics, including active
   revision resolution, all windows, ACTUAL matching/adherence/substitutions,
   offset-aware time handling, and arbitrary cycles.
4. Port progression and adaptive coaching through `TrainingEngine`.
5. Add Python-authored shared fixture families for evaluation, generation,
   history, progression, and adaptation; Swift must pass every supported row.
6. Update docs/capability matrix/roadmap truthfully to state Swift's actual
   scope and defer Kotlin/R core-engine completion to future releases.

## Release conditions

Do not prepare/tag/release until the Swift-focused release gate is written and
met: full Swift fixture parity, isolated Swift consumer coverage for the full
engine, complete repository suite green, audit documentation updated, and CI
green on the exact human implementation and release-prep commits.

No Python bridge, network dependency, LLM integration, UI, or v1.12 feature
work is in scope.
