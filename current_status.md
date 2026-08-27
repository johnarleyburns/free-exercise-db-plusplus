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

## Repository state

- Branch: `main`
- Last committed HEAD before this work: `564272a release: prepare v1.11.0`
- That release-preparation commit is superseded. **Do not tag or release it.**
- No `v1.11.0` tag has been created.
- The working tree contains uncommitted Swift/Kotlin engine-foundation work.
  Inspect it before committing; do not discard it.

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

## Immediate next task: Swift canonical engine port

Port the Python reference incrementally, using these files as the oracle:

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
