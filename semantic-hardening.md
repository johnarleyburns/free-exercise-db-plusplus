# Free Exercise DB++ — Semantic Hardening

Status: **required remediation before further feature expansion**  
Audience: Codex CLI / maintainers  
Scope: **analysis semantic correctness only**  
Priority: **high**

## 1. Goal

The PLAN / ACTUAL / TARGET / ANALYSIS architecture is largely implemented, but several semantic issues remain. Fix them before adding new features.

Preserve:

- stable Free Exercise DB++ v1 exercise-definition contract;
- PLAN / ACTUAL / TARGET / ANALYSIS separation;
- explicit-reference-first matching;
- no fuzzy matching by default;
- DB++ direct / indirect / stabilizer roles;
- arbitrary non-7-day plan cycles;
- custom/unmapped exercise support;
- backward compatibility where practical.

This is a correctness, reproducibility, and research/trainer reliability sprint.

## 2. Files to inspect

At minimum:

```text
src/analysis/coverage.py
src/analysis/policies.py
src/analysis/plan_actual.py
src/analysis/plan_compare.py
src/analysis/targets.py
src/analysis/matching.py
src/analysis/export.py
src/analysis/units.py
src/plan/validate_plan.py

workout-plan.schema.json
volume-target.schema.json
workout.schema.json

tests/analysis/
tests/plan/
tests/target/
tests/workout/

docs/PLAN-ANALYSIS.md
docs/PLAN-ACTUAL.md
docs/PLAN-COMPARISON.md
docs/VOLUME-TARGETS.md
docs/WORKOUT-PLAN.md
README.md

packages/python/
packages/swift/
packages/kotlin/
packages/r/

.github/workflows/build-db.yml
```

Do not edit unrelated DB++ exercise mappings unless a test reveals a genuine unrelated defect.


## 3. Authoritative set credits

Analysis must not hard-code `1.0 / 0.5 / 0.0`. Read the authoritative values from:

```text
metadata.setCredits
```

Create one shared helper that works with both raw DB dictionaries and consumer Database objects.

Use it everywhere effective-set values are calculated and everywhere analysis metadata reports credits.

Acceptance test: a synthetic DB using:

```json
{
  "metadata": {
    "setCredits": {
      "direct": 2.0,
      "indirect": 0.25,
      "stabilizer": 0.1
    }
  }
}
```

must cause analysis to use exactly those values.

The shipped DB remains `1.0 / 0.5 / 0.0`; the point is that the DB, not analyzer source code, is authoritative.

## 4. `volumeEligible=false`

For resistance-volume analysis:

```text
volumeEligible=false
=> no direct muscle set contribution
=> no indirect muscle set contribution
=> no stabilizer participation contribution
=> no effective-set contribution
=> no resistance-volume movement-pattern contribution
```

Still report the prescription as mapped and volume-ineligible:

```text
mappedSets
ineligibleSets
ineligiblePrescriptions
```

If generic movement participation is useful later, expose it separately; do not mix it into resistance-volume coverage.

Acceptance test: two sets of a `volumeEligible=false` shoulder mobility exercise produce zero muscle coverage and zero `movementPatternSets`, while `ineligibleSets == 2`.

## 5. Preserve PLAN ranges

Do not collapse:

```json
{"min": 3, "target": 4, "max": 5}
```

into only `4` as the canonical analysis representation.

Create shared range helpers such as:

```python
normalize_range(value)
add_ranges(a, b)
scale_range(value, factor)
```

Scalar prescriptions normalize to equal min/target/max values.

Preserve min/target/max through:

- direct sets;
- indirect sets;
- stabilizer participation;
- effective sets;
- movement-pattern sets;
- native-cycle totals;
- seven-day normalization;
- target comparison;
- exports.

Example expected output:

```json
"effectiveSetRanges": {
  "chest": {"min": 3.0, "target": 4.0, "max": 5.0}
}
```

If existing scalar keys are public, preserve them as target/convenience views rather than silently changing numbers into objects.

Acceptance test: bench 3/4/5 sets yields chest direct 3/4/5 and indirect triceps effective 1.5/2.0/2.5.


## 6. Explicit analysis policy

`src/analysis/policies.py` must define an explicit built-in policy:

```text
dbpp-default-volume-v1
```

Recommended default semantics:

```text
working      count
backoff      count
amrap        count
drop         count once at parent-set level
cluster      count once at parent-set level
rest_pause   count once at parent-set level
warmup       exclude
technique    exclude
test         exclude by default
isometric    exclude by default from resistance-set volume
assisted     count when it is a working parent set
other        exclude by default
```

Align names to actual schema enums.

This policy controls set counting only. It must not change DB++ credits based on RPE, RIR, load, tempo, or failure.

Every analysis result must record:

```json
"analysisPolicy": "dbpp-default-volume-v1"
```

Acceptance test: 2 warmups + 3 working + 1 technique set = 3 counted sets.

Macro-segments inside a drop/cluster/rest-pause parent set do not multiply the parent set count.

For unilateral work, do not silently duplicate a top-level set because it is unilateral. Explicit separately recorded left/right top-level sets remain separate observations.


## 7. Unplanned ACTUAL coverage

Current PLAN-vs-ACTUAL analysis must be changed so `unplanned_addition` work contributes to ACTUAL totals.

Separate ACTUAL coverage into:

```text
matched
substitutions
unplanned
total
```

Recommended result shape:

```json
"actualCoverage": {
  "matched": {},
  "substitution": {},
  "unplanned": {},
  "total": {}
}
```

`total` includes every counted, known DB++ ACTUAL exercise, whether prescribed or not.

Unknown/custom ACTUAL exercises remain coverage-incomplete and must be reported.

Unplanned work must not satisfy an unrelated missing prescription.

Also expose:

```text
plannedCoverage
matchedActualCoverage
unplannedActualCoverage
totalActualCoverage
```

so users can answer both adherence and total-work questions.

Acceptance case:

```text
PLAN: Bench 3
ACTUAL: Bench 3 + Lateral Raise 4
```

Bench adherence is 100%; lateral raises are unplanned; total ACTUAL shoulder coverage includes them.


## 8. PLAN 0.1 vs 0.2 schema semantics

A document declaring:

```json
"schemaVersion": "0.1.0"
```

must not use 0.2-only fields.

A `0.2.0` document may use them.

Audit the current schema to identify all 0.2-only fields, including likely:

```text
phases
phaseId
plannedSets
setPrescriptionId
progression
optional/conditional prescription fields
```

Use JSON Schema conditional logic and/or deterministic semantic validation.

Acceptance: `0.1.0` + `phases` fails; identical valid `0.2.0` form passes.

## 9. Aggregate prescription XOR explicit `plannedSets`

Exactly one style is permitted:

```text
aggregate:
  sets/reps (+ optional load/effort)

OR

explicit:
  plannedSets[]
```

Reject ambiguous documents containing both aggregate set prescription and `plannedSets`.

Use `oneOf` or semantic validation.

No analyzer should have to choose precedence between both forms.


## 10. Set-level prescription matching

Hardening order:

1. explicit `setPrescriptionId`;
2. positional fallback only when no explicit ID exists and correspondence is unambiguous;
3. otherwise mark mismatch/unplanned.

Never consume one planned set twice.

Never positionally rematch an explicit but invalid `setPrescriptionId`.

Preserve/set statuses as applicable:

```text
matched
substitution
unplanned_addition
missing_prescription
incomplete
unable_to_match
```

For heterogeneous planned sets, compare each ACTUAL set to its own planned reps/load/effort, not to exercise-level aggregate fields.

Tests must cover:

- explicit set ID;
- positional fallback;
- invalid explicit set ID;
- missing planned set;
- extra ACTUAL set;
- incomplete ACTUAL set;
- heterogeneous top/backoff sets.


## 11. Periodization corrections

Honor phase-specific cycle lengths:

```text
phase.cycle.lengthDays if present
else root cycle.lengthDays
```

Normalize each phase separately to seven days.

Do not blindly use root cycle duration for every phase.

Duration-weight phase averages:

```text
weighted average =
Σ(phase volume × durationCycles)
/
Σ(durationCycles)
```

Do this for min/target/max once ranges are propagated.

If phase cycle lengths differ, expose both:

- native per-cycle values;
- seven-day normalized values.

Acceptance:

```text
Phase A = 3 cycles @ 12 normalized chest sets
Phase B = 1 cycle  @ 4 normalized chest sets
```

weighted normalized average must be `10`, not `8`.

Add a separate test with root cycle 7, phase A 8 days, phase B 6 days.


## 12. TARGET hardening

Use richer states:

```text
below_minimum
within_range_below_target
at_target
within_range_above_target
above_maximum
not_targeted
```

For target profiles without a midpoint, `within_range` is acceptable; do not invent a target.

Return at least:

```text
actualEffectiveSets
minimum
target
maximum
differenceFromTarget
state
periodDays
```

For ranged PLAN coverage, return the PLAN range too. Headline comparison may initially use PLAN target coverage if documented.

Add optional DB-aware validation:

```python
validate_target(target, db=db)
```

Validate muscle IDs against the authoritative DB++ muscle ontology.

Keep schema-only validation possible without DB context.

Unknown target muscles must produce deterministic semantic errors.


## 13. Adherence dimensions

PLAN-vs-ACTUAL muscle adherence must expose separately:

```text
direct
indirect
stabilizer participation
effective
```

For each metric return:

```text
planned
actual
delta
fraction
```

Do not collapse everything to effective sets.

Also expose:

### Exercise adherence

```text
strictPrescriptionAdherence
substitutionAdjustedCompletion
```

An explicitly substituted exercise is not an exact identity match.

### Set-range adherence

For a 3/4/5 set prescription and 4 actual sets expose, at minimum:

```text
meetsMinimum
meetsTarget
withinMaximum
differenceFromTarget
```

Do not reduce ranged adherence to one percentage.

## 14. Load adherence

Only compare compatible representations.

Safe examples:

```text
kg ↔ kg
lb ↔ lb
kg ↔ lb via known conversion
```

Do not compare machine levels, arbitrary band labels, and kilograms as equivalent.

Use `src/analysis/units.py`.

Return:

```text
planned
actual
delta
withinRange
comparable
reason (when not comparable)
```

## 15. RPE/RIR adherence

Compare RPE to planned RPE and RIR to planned RIR independently.

Do not infer RPE from RIR or vice versa.

Return range membership and target delta where available.

## 16. Volume-load adherence

Where mass-like load is comparable:

```text
volumeLoad = Σ(reps × normalized load)
```

Return planned, actual, delta, fraction, and `comparable`.

Do not compute for incompatible resistance modes, unknown units, band labels, machine levels, or bodyweight unless required mass is explicitly present.

Do not infer body mass.


## 17. No universal stimulus score

Do not introduce project-default formulas such as:

```text
effective sets × RPE
effective sets × load
effective sets × RIR weighting
```

Keep set coverage, intensity, effort, and volume-load as separate analyses.

## 18. Muscle exposure frequency

Implement PLAN exposure frequency.

Definition:

> A muscle receives one exposure in a session when at least one counted, volume-eligible set contributes a direct or indirect role to that muscle.

Stabilizer-only participation does not count as muscle-volume exposure by default.

Return:

```text
exposuresPerNativeCycle
normalizedExposuresPer7Days
```

Also implement movement-pattern exposure frequency if straightforward.

Preserve existing exercise prescription frequency separately and name each frequency measure clearly.


## 19. Analysis provenance

Every analysis result must include enough metadata for reproducibility, where available:

```text
analysisVersion
analysisPolicy
dbSchemaVersion
dbConverterVersion
dbUpstreamSha256
planSchemaVersion
workoutSchemaVersion
targetSchemaVersion
setCredits actually used
nativePeriodDays
normalizedPeriodDays
rangePolicy
unitPolicy/version
```

PLAN-vs-PLAN should identify both plan schema versions if they differ.

PLAN-vs-ACTUAL must include the ACTUAL schema version.

TARGET comparison must include target schema version.

## 20. Coverage completeness

Preserve and extend diagnostics.

PLAN:

```text
plannedSets
mappedSets
unmappedSets
ineligibleSets
mappedFraction
```

ACTUAL:

```text
actualCountedSets
mappedActualSets
unmappedActualSets
ineligibleActualSets
mappedFraction
```

PLAN-vs-ACTUAL reports both independently.

Never present apparently complete muscle totals without completeness metadata.


## 21. Research exports

Keep existing generic exports.

Add deterministic muscle-level research output with columns like:

```text
subject_id
session_id
plan_id
revision_id
plan_session_id
phase_id
period
muscle
planned_direct_sets
actual_direct_sets
planned_indirect_sets
actual_indirect_sets
planned_stabilizer_sets
actual_stabilizer_sets
planned_effective_sets
actual_effective_sets
effective_adherence_fraction
analysis_policy
db_schema_version
db_converter_version
plan_schema_version
workout_schema_version
```

Use empty values when identifiers are unavailable.

Add exercise-level export:

```text
subject_id
session_id
prescription_id
planned_exercise_id
actual_exercise_id
match_status
planned_sets
actual_sets
```

For ranged PLAN values include min/target/max fields rather than flattening them.

Do not remove existing generic CSV APIs.


## 22. Documentation

Synchronize:

```text
docs/PLAN-ANALYSIS.md
docs/PLAN-ACTUAL.md
docs/PLAN-COMPARISON.md
docs/VOLUME-TARGETS.md
docs/WORKOUT-PLAN.md
README.md
```

Document:

- credits come from DB metadata;
- `volumeEligible=false` exclusion;
- `dbpp-default-volume-v1`;
- ranged PLAN coverage;
- unplanned ACTUAL coverage;
- separate adherence dimensions;
- phase cycle handling and duration weighting;
- set-level matching;
- TARGET states;
- analysis provenance;
- research exports.

Do not claim unimplemented parity/export capabilities.

## 23. Consumer package parity

Root Python semantics are the reference.

### Python

Installed wheel must be standalone and must not import repository-level `src.*`.

Prefer one canonical implementation or controlled package vendoring/synchronization rather than divergent copies.

### Swift / Kotlin / R

Supported plan-coverage functions must not contradict root semantics.

It is acceptable for advanced PLAN-vs-ACTUAL adherence features to remain Python-only temporarily, but docs must state actual capability.

Do not claim parity that is not implemented.


## 24. CI and regression tests

CI must run every new semantic test.

Required coverage:

```text
DB metadata set credits
volumeEligible exclusion
range propagation
default set-type policy
drop/cluster/rest-pause parent counting
unilateral counting
unplanned ACTUAL total coverage
PLAN 0.1 vs 0.2 version enforcement
aggregate XOR plannedSets
setPrescriptionId exact matching
invalid explicit setPrescriptionId
phase-specific cycles
duration-weighted phase averages
TARGET states
TARGET DB muscle validation
direct/indirect/stabilizer/effective adherence
load adherence
RPE adherence
RIR adherence
volume-load compatible and incompatible cases
muscle exposure frequency
analysis provenance
research exports
```

Keep all existing:

```text
release-contract
golden mappings
medium-confidence policy
workout fixtures
PLAN fixtures
TARGET fixtures
Python package
Swift
Kotlin
R
interop mapping checks
```

## 25. Comprehensive semantic golden fixture

Create one small synthetic DB + PLAN + ACTUAL + TARGET fixture designed for hand calculation.

PLAN should include:

```text
8-day cycle
Bench 3/4/5 sets
Row using heterogeneous plannedSets
one volumeEligible=false mobility exercise
one lower-body exercise
```

ACTUAL should include:

```text
partially completed bench
row sets linked by setPrescriptionId
explicit substitution
unplanned lateral raises
warmup set
incomplete set
```

TARGET should include:

```text
chest min/target/max
back minimum
shoulder maximum
```

Assert exact outputs.

This fixture should be the primary semantic regression anchor.


## 26. Required outcomes

After remediation all statements below must be true:

1. Effective-set credits come from DB metadata.
2. `volumeEligible=false` contributes no resistance-volume muscle or pattern totals.
3. Ranged prescriptions preserve min/target/max coverage.
4. Default counting is policy-driven and named.
5. Warmups do not count under the default policy.
6. Drop/cluster/rest-pause macro-segments do not multiply parent set count.
7. Unplanned ACTUAL work contributes to total ACTUAL coverage.
8. Unplanned ACTUAL work does not satisfy unrelated prescriptions.
9. PLAN 0.1 cannot use PLAN 0.2-only fields.
10. Aggregate sets/reps and `plannedSets` are mutually exclusive.
11. Explicit setPrescriptionId takes precedence.
12. Invalid explicit set references are not silently rematched.
13. Phase-specific cycle lengths are honored.
14. Phase averages are duration-weighted.
15. TARGET states distinguish below/at/above target within range.
16. Target muscle IDs can be validated against DB++.
17. Muscle adherence exposes direct, indirect, stabilizer, and effective values separately.
18. Load/RPE/RIR adherence is only computed when meaningful.
19. Volume-load is not computed for incompatible resistance modes.
20. Muscle exposure frequency is available.
21. Analysis metadata is sufficient for reproduction.
22. Research CSV output is deterministic.


## 27. Non-goals

Do not add:

- new exercise taxonomy;
- exercise family graphs;
- fine-grained anatomy;
- fuzzy/AI matching;
- injury-risk analysis;
- hypertrophy optimization recommendations;
- unrelated external exporters;
- alternative set-credit models;
- automatic target recommendations;
- arbitrary progression execution engine;
- database backend;
- mandatory pandas;
- mandatory Parquet.

## 28. Implementation order

Use this order:

```text
1. shared credits + range helpers
2. policy enforcement
3. volumeEligible fix
4. range-aware PLAN coverage
5. phase cycle + weighted averages
6. PLAN version/XOR validation
7. ACTUAL coverage separation
8. set-level matching hardening
9. direct/indirect/effective adherence
10. TARGET semantics
11. load/RPE/RIR/volume-load adherence
12. muscle/pattern frequency
13. provenance
14. research exports
15. package parity
16. docs
17. full CI
```

Run tests after each logical group.


## 29. Codex execution prompt

Use this as the operative task:

```text
Read semantic-hardening.md, ROADMAP.md, current_status.md, and the current repository.

Implement the entire semantic-hardening remediation.

This is a correctness sprint, not a feature-expansion sprint.

Priority:
1. analysis correctness
2. schema semantic correctness
3. reproducibility
4. regression tests
5. consumer parity
6. documentation

Guardrails:
- Do not change the stable Free Exercise DB++ v1 exercise-definition contract.
- Do not change direct/indirect/stabilizer meanings.
- Read set-credit values from DB metadata; do not hard-code them.
- Do not use fuzzy matching.
- Do not infer physiological equivalence for substitutions.
- Do not create a universal stimulus score.
- Do not add unrelated interop exporters.
- Preserve PLAN / ACTUAL / TARGET / ANALYSIS separation.

Run the complete existing test suite plus all new tests.

Before finishing, report:
- files changed
- semantic decisions made
- tests added
- intentionally deferred items
- exact commands run
- confirmation that all CI-equivalent tests pass
```

## 30. Validation commands

At minimum run all root Python tests:

```bash
PYTHONPATH=. bash -c '
for t in $(find tests -name "test_*.py" -type f | sort); do
  echo "== $t =="
  python3 "$t" free-exercise-db-plusplus.json || exit $?
done
'
```

Run all Python package tests:

```bash
PYTHONPATH=packages/python:. bash -c '
for t in $(find packages/python/tests -name "test_*.py" -type f | sort); do
  echo "== $t =="
  python3 "$t" || exit $?
done
'
```

Also:

```bash
swift test --package-path packages/swift/FreeExerciseDBPlusPlus
```

Run Kotlin and R tests using the current CI commands.

Build and install the Python wheel in an isolated temporary environment and run package analysis outside the repository checkout.

Run schema/example validation and the full CI-equivalent checks where practical.

Compilation alone is not sufficient.

## 31. Release gate

Do not resume the next roadmap feature phase until:

```text
all P0 semantic issues are fixed
all P1 semantic issues are fixed
all regression tests pass
CI is green
docs match behavior
```

At that point the PLAN / ACTUAL / TARGET / ANALYSIS layer can be treated as sufficiently hardened for broader trainer/research use and further interoperability work.

