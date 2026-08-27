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
- Part C — canonical comparison rules: pending Part B
- Parts D–N — Swift engine architecture and parity: pending the preceding
  parts and the detailed order in `HANDOFF.md`

### Resume instructions for the next phase

Begin Part C by defining the normalized field-by-field comparison contract
for the five new engine fixture families. Do not begin Swift implementation
work in the same cycle; preserve the existing intent fixtures and do not work
on Kotlin or R.

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

Part B commit: pending commit after review.

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
- Current committed HEAD before the next implementation phase: `ac0e0a3`
  (`begun kotlin port`)
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
