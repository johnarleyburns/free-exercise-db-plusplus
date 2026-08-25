# Free Exercise DB++ — Post-1.0 Roadmap

Status: **post-v1.0.0**  
Implementation status: **Sprints 1-9 complete; overall success criterion 14 remains partial pending a validated ACTUAL exporter.**
Primary focus: **Workout PLAN + ACTUAL + TARGET + ANALYSIS**, followed by external interoperability mappings  
Audience: maintainers and implementation agents, including Codex CLI

## 1. Direction

Free Exercise DB++ v1.0.0 established a stable, evidence-audited exercise-definition database with stable `exerciseId` values, normalized movement patterns and muscle roles, direct/indirect/stabilizer semantics, `1.0 / 0.5 / 0.0` set credits, embedded evidence provenance, confidence metadata, reproducible builds, and release automation.

The repository has already implemented Workout ACTUAL schema 0.2.0 and substantial interoperability scaffolding. The next phase should avoid bloating the core exercise-definition schema and add prescription/analysis layers around the stable vocabulary. The original three-layer model remains useful, but is now expanded by PLAN, TARGET, and ANALYSIS.

```text
1. Exercise vocabulary
   free-exercise-db-plusplus.json

2. Workout ACTUAL observation format
   workout.schema.json

3. Workout PLAN prescription format
   workout-plan.schema.json

4. Volume TARGET criteria
   volume-target.schema.json

5. Derived ANALYSIS layer
   src/analysis/*

6. Interoperability translation layer
   mappings/*
```

Architectural rule:

> Keep exercise definitions, workout observations, and external-format mappings separate.

## 2. Strategic priorities

### Priority A — PLAN + ACTUAL + TARGET + ANALYSIS

Workout ACTUAL 0.2 is already implemented. The next goal is to add a separate prescription format, target profiles, and deterministic analysis while continuing to mature ACTUAL only where PLAN linkage requires it. Together these layers should support:

- personal training logs;
- coach/athlete exchange;
- app import/export;
- research datasets;
- longitudinal volume analysis;
- effective-set calculation using DB++;
- Python and Swift round-trip interchange.

The workout format should use DB++ `exerciseId` when possible but still represent custom exercises.

### Priority B — Interoperability mappings

Create explicit mapping layers for:

1. Garmin FIT
2. Apple HealthKit
3. Android Health Connect
4. HL7 FHIR Physical Activity
5. IEEE 1752.1 / Open mHealth concepts

Every mapping should classify each field as:

```text
exact
compatible
lossy
extension_required
unsupported
```

Do not contaminate the native DB++ or workout schema with target-specific fields.

### Priority C — Consumer tooling

After schema stabilization:

- Python loader/helper package;
- Swift package;
- examples and validators;
- effective-set reference implementation.

### Priority D — Scientific/taxonomy enrichment

Only after workout/interoperability work is stable:

- laterality;
- kinetic chain;
- movement plane;
- joint actions;
- exercise family relationships;
- optional fine-grained anatomy;
- richer evidence metadata.

## 3. Recommended release sequence

The repository has already implemented Workout ACTUAL 0.2.0 and interop scaffolding, so the post-1.0 sequence is now:

```text
v1.1.x    Workout PLAN 0.1 + TARGET 0.1 + plan coverage/gap analysis
v1.2.x    Workout ACTUAL 0.3 planning links + PLAN-vs-ACTUAL adherence
v1.3.x    Periodized PLAN 0.2 + research exports + comparison polish
v1.4.x    PLAN/ACTUAL interoperability refinement
v1.5.x    Python package stabilization + Swift parity
v1.6.x+   taxonomy, exercise-family, anatomy, and evidence enrichment

v2.0.0    Only for genuinely breaking core exercise-DB contract changes
```

Version the auxiliary contracts independently:

```text
workout.schema.json       0.2.0 current -> 0.3 planning links -> 0.9 RC -> 1.0 stable ACTUAL
workout-plan.schema.json  0.1 basic PLAN -> 0.2 phases -> 0.9 RC -> 1.0 stable PLAN
volume-target.schema.json 0.1 small target contract -> 1.0 once semantics are proven
interop mappings          independent mapping versions per target
```

## 4. Target repository structure

```text
.
├── README.md
├── LICENSE
├── free-exercise-db-plusplus.json
├── free-exercise-db-plusplus.schema.json
├── workout.schema.json
├── workout-plan.schema.json
├── volume-target.schema.json
├── interop-mapping.schema.json
├── src/
│   ├── convert_fedb_to_fedbpp.py
│   ├── workout/
│   │   ├── validate_workout.py
│   │   └── migrate_workout.py
│   ├── plan/
│   │   └── validate_plan.py
│   ├── analysis/
│   │   ├── coverage.py
│   │   ├── plan_volume.py
│   │   ├── plan_compare.py
│   │   ├── plan_actual.py
│   │   ├── targets.py
│   │   ├── matching.py
│   │   ├── units.py
│   │   └── export.py
│   └── interop/
│       ├── common.py
│       ├── garmin_fit.py
│       ├── healthkit.py
│       ├── health_connect.py
│       ├── fhir.py
│       └── open_mhealth.py
├── tests/
│   ├── workout/
│   └── interop/
├── docs/
│   ├── WORKOUT-INTERCHANGE.md
│   ├── INTEROP.md
│   ├── INTEROP-GARMIN-FIT.md
│   ├── INTEROP-HEALTHKIT.md
│   ├── INTEROP-HEALTH-CONNECT.md
│   ├── INTEROP-FHIR.md
│   ├── INTEROP-OPEN-MHEALTH.md
│   └── adr/
├── mappings/
│   ├── garmin-fit.json
│   ├── healthkit.json
│   ├── health-connect.json
│   ├── fhir.json
│   └── open-mhealth.json
├── examples/
│   ├── workouts/
│   └── interop/
└── packages/
    ├── python/
    └── swift/
```

Keep the main JSON and both schemas at repository root for stable public URLs.

# 5. Workout interchange architecture

Use:

```text
Athlete
  ↓
Training Session
  ↓
Exercise Observation
  ↓
Set Observation
  ↓
Rep Observation (optional)
```

Rep-level data must remain optional.

Example:

```json
{
  "schemaVersion": "0.2.0",
  "sessionId": "2026-08-24-upper-a",
  "athleteId": "athlete-123",
  "startTime": "2026-08-24T14:00:00-04:00",
  "endTime": "2026-08-24T15:20:00-04:00",
  "exercises": []
}
```

## 6. Workout design principles

### Stable exercise reference

Preferred:

```json
{
  "exerciseId": "Barbell_Bench_Press_-_Medium_Grip"
}
```

Custom exercise fallback:

```json
{
  "exerciseId": null,
  "exerciseName": "Custom Cable Press",
  "externalExerciseId": {
    "system": "com.example.trainingapp",
    "value": "exercise-998"
  }
}
```

Never require DB++ modification just to record an app-specific exercise.

### Explicit quantities

Use:

```json
{
  "value": 100,
  "unit": "kg"
}
```

Prefer UCUM-compatible units where practical:

```text
kg
lb
s
min
m
km
m/s
W
```

### Observation-first

Store what happened, not derived analytics.

Do not store required fields for:

- weekly muscle sets;
- fatigue models;
- volume trends;
- calculated muscle tonnage.

Those belong in analysis output.

# 7. Workout schema fields

## Session

Required:

- `schemaVersion`
- `sessionId`
- `startTime`
- `exercises`

Optional:

- `endTime`
- `athleteId`
- `coachId`
- `programId`
- `programDayId`
- `timezone`
- `location`
- `notes`
- `tags`
- `source`
- `device`
- `software`

## Exercise observation

Recommended fields:

- `exerciseId`
- `exerciseName`
- `externalExerciseId`
- `variation`
- `equipment`
- `order`
- `laterality`
- `notes`
- `tags`
- `sets`

Example:

```json
{
  "exerciseId": "Barbell_Back_Squat",
  "order": 1,
  "laterality": "bilateral",
  "sets": []
}
```

## Set observation

Example:

```json
{
  "setNumber": 3,
  "setType": "working",
  "reps": 8,
  "load": {
    "value": 100,
    "unit": "kg"
  },
  "rpe": 8,
  "rir": 2,
  "completed": true
}
```

Recommended fields:

- `setNumber`
- `setType`
- `reps`
- `load`
- `duration`
- `distance`
- `rpe`
- `rir`
- `tempo`
- `restAfter`
- `toFailure`
- `completed`
- `assistance`
- `notes`
- `segments`
- `repetitions`

Controlled set types:

```text
warmup
working
backoff
drop
amrap
technique
test
isometric
cluster
rest_pause
assisted
other
```

# 8. Supersets, circuits, and complexes

Do not encode them as set types.

Recommended:

```json
"structure": {
  "groupId": "A",
  "groupType": "superset",
  "round": 2
}
```

Controlled group types:

```text
superset
tri_set
giant_set
circuit
complex
paired
```

# 9. Drop sets and intra-set structure

Recommended macro-segment representation:

```json
{
  "setNumber": 3,
  "setType": "drop",
  "segments": [
    {"reps": 8, "load": {"value": 80, "unit": "kg"}},
    {"reps": 6, "load": {"value": 60, "unit": "kg"}},
    {"reps": 5, "load": {"value": 40, "unit": "kg"}}
  ]
}
```

Policy:

- `segments` = macro-structure inside one set;
- `repetitions` = optional individual-rep telemetry.

Use the same mechanism for rest-pause and cluster work.

# 10. Laterality

Allow:

```text
bilateral
left
right
alternating
unspecified
```

Exercise-level laterality may be overridden at set level.

# 11. Tempo

Before workout schema 1.0 choose one canonical representation.

Preferred eventual form:

```json
{
  "eccentric": 3,
  "bottom": 1,
  "concentric": "X",
  "top": 0
}
```

A string such as `"3-1-X-0"` is acceptable during early 0.x design.

# 12. Failure / RPE / RIR

Keep independent:

```json
{
  "rpe": 9,
  "rir": 1,
  "toFailure": false
}
```

Do not infer one from another in the interchange format.

# 13. Isometrics and cardio

Isometric:

```json
{
  "setType": "isometric",
  "duration": {"value": 30, "unit": "s"}
}
```

Mixed/cardio:

```json
{
  "duration": {"value": 20, "unit": "min"},
  "distance": {"value": 5, "unit": "km"}
}
```

DB++ `volumeEligible` determines whether resistance-volume analytics apply.

# 14. Velocity-based training

Optional set fields:

```json
{
  "meanVelocity": {"value": 0.62, "unit": "m/s"},
  "peakVelocity": {"value": 1.03, "unit": "m/s"}
}
```

Optional rep-level telemetry:

```json
{
  "repNumber": 4,
  "duration": {"value": 2.1, "unit": "s"},
  "meanVelocity": {"value": 0.55, "unit": "m/s"},
  "rangeOfMotion": {"value": 0.54, "unit": "m"},
  "completed": true
}
```

# 15. Resistance model

This needs explicit design before workout schema 1.0.

Recommended:

```json
"resistance": {
  "mode": "bodyweight_plus_load",
  "externalLoad": {
    "value": 20,
    "unit": "kg"
  }
}
```

Modes:

```text
external_load
bodyweight
bodyweight_plus_load
assisted_bodyweight
band
machine_setting
unknown
```

Weighted pull-up:

```json
{
  "mode": "bodyweight_plus_load",
  "externalLoad": {"value": 20, "unit": "kg"}
}
```

Assisted pull-up:

```json
{
  "mode": "assisted_bodyweight",
  "assistance": {"value": 30, "unit": "kg"}
}
```

Do not infer total system mass unless athlete body mass is explicitly available.

Machine setting:

```json
{
  "mode": "machine_setting",
  "value": 8,
  "unit": "level"
}
```

Band:

```json
{
  "mode": "band",
  "band": {
    "manufacturer": null,
    "label": "heavy",
    "nominalResistance": null
  }
}
```

# 16. Provenance

Support:

```json
{
  "source": {
    "system": "com.example.workoutapp",
    "version": "3.2.1",
    "recordId": "abc123"
  }
}
```

Optional device metadata:

```json
{
  "device": {
    "manufacturer": "Apple",
    "model": "Watch"
  }
}
```

Avoid device serial numbers by default.

# 17. Extension mechanism

Recommended:

```json
{
  "extensions": {
    "com.example.myapp": {
      "foo": "bar"
    }
  }
}
```

Rules:

- reverse-domain namespace;
- extension value must be an object;
- consumers may ignore unknown extensions;
- extensions must never override core semantics.

# 18. Workout migrations

Create:

```text
src/workout/migrate_workout.py
```

Support only forward migrations:

```text
0.1.x -> 0.2.x -> ... -> 1.0.0
```

Requirements:

- deterministic;
- preserve unknown extensions;
- non-destructive where possible;
- golden migration tests.

# 19. Workout test matrix

Create valid examples for:

1. basic barbell strength;
2. hypertrophy machine workout;
3. bodyweight workout;
4. timed isometric;
5. mixed cardio + resistance;
6. unilateral left/right;
7. alternating;
8. superset;
9. circuit;
10. drop set;
11. AMRAP;
12. rest-pause;
13. cluster;
14. assisted reps;
15. velocity-based training;
16. custom/unmapped exercise;
17. aborted/incomplete set;
18. rep-level telemetry.

Also create intentionally invalid fixtures.

CI must assert valid examples pass and invalid examples fail.

# 20. Python consumer package

Later target:

```text
packages/python/fedbpp/
```

Possible API:

```python
from fedbpp import Database, Workout

db = Database.load("free-exercise-db-plusplus.json")
workout = Workout.load("workout.json")

volume = workout.effective_sets(db)
```

Useful helpers:

- `get_exercise(id)`
- `find_exercises(query)`
- `exercises_for_muscle(muscle)`
- `validate_workout(workout)`
- `migrate_workout(workout)`
- `effective_sets(workout)`
- `weekly_volume(workouts)`

Do not require pandas.

# 21. Swift package

Target:

```text
packages/swift/FreeExerciseDBPlusPlus/
```

Requirements:

- Swift 6;
- `Codable`;
- `Sendable`;
- Foundation-only if practical;
- macOS/iOS/watchOS support where reasonable.

Potential API:

```swift
let database = try FEDatabase.load(url: dbURL)
let workout = try Workout.load(url: workoutURL)
let volume = workout.effectiveSets(using: database)
```

# 22. Interoperability architecture

Every target should have:

```text
mappings/<target>.json
docs/INTEROP-<TARGET>.md
src/interop/<target>.py
tests/interop/test_<target>.py
```

Declarative mapping entry:

```json
{
  "sourcePath": "exercises[].sets[].reps",
  "targetPath": "...",
  "quality": "exact",
  "transform": null,
  "notes": null
}
```

Mapping quality enum:

```text
exact
compatible
lossy
extension_required
unsupported
```

# 23. Mapping-registry schema

Create:

```text
interop-mapping.schema.json
```

Example:

```json
{
  "target": "garmin-fit",
  "mappingVersion": "0.1.0",
  "entries": [
    {
      "source": {
        "exerciseId": "Pullups"
      },
      "target": {
        "code": "PULL_UP"
      },
      "quality": "compatible",
      "notes": null
    }
  ]
}
```

Version mappings independently.

# 24. Garmin FIT

Goals:

- session timestamps;
- exercise identity;
- reps;
- load/resistance;
- set type where possible;
- duration;
- distance.

Maintain:

```text
DB++ exerciseId
     ↓
Garmin exercise category/name enum
```

Allow:

```text
exact
nearest
unmapped
```

Never replace DB++ identity with Garmin enums.

First deliverables:

```text
mappings/garmin-fit.json
docs/INTEROP-GARMIN-FIT.md
```

Implement import/export code only after the declarative mapping is reviewed.

# 25. Apple HealthKit

Treat HealthKit mainly as workout/session metadata plus selected measurements.

Map:

- workout start/end;
- activity type;
- distance;
- energy;
- selected biometric references if appropriate;
- stable linkage metadata.

DB++ workout JSON remains the source of truth for set-level strength data.

Document what is lost during HealthKit export.

# 26. Android Health Connect

Use the same philosophy as HealthKit.

Investigate current support for:

- exercise sessions;
- repetitions;
- distance;
- duration;
- source/device metadata.

Keep DB++ workout JSON as the high-fidelity native representation.

# 27. HL7 FHIR

FHIR is an export/import layer, not the native workout format.

Potential concepts/resources:

- `Observation`;
- `Procedure`;
- Physical Activity implementation-guide profiles where applicable.

Conceptual model:

```text
DB++ exercise definition = concept/terminology
Workout exercise/set      = event/observation
Load/reps/RPE             = measurements
Session                    = grouping context
```

Deliver:

```text
mappings/fhir.json
docs/INTEROP-FHIR.md
examples/interop/fhir/
```

Do not claim formal conformance until examples pass official FHIR validation.

# 28. IEEE 1752.1 / Open mHealth

Use primarily for:

- provenance;
- activity episode metadata;
- units;
- timestamps;
- research export conventions.

Document where DB++ is intentionally more granular for resistance training.

# 29. Interop development phases

## A. Documentation

For each target, create a field mapping table:

| DB++ / Workout field | External field | Quality | Notes |
|---|---|---|---|

## B. Declarative mappings

Create mapping JSON files and validate against `interop-mapping.schema.json`.

## C. Export prototypes

Start with FHIR JSON and consumer-platform metadata exports.

## D. Import

Only add import where identity can be recovered safely.

Never silently fuzzy-match exercise identity.

# 30. Exercise taxonomy enrichment

After workout/interoperability stabilization, add optional fields such as:

```json
"biomechanics": {
  "laterality": "bilateral",
  "kineticChain": "closed",
  "planes": ["sagittal"],
  "jointActions": [
    "hip_extension",
    "knee_extension"
  ]
}
```

Possible controlled values:

Laterality:

```text
bilateral
unilateral
alternating
mixed
```

Kinetic chain:

```text
open
closed
mixed
unknown
```

Planes:

```text
sagittal
frontal
transverse
multiplanar
```

Keep additions optional and compatible within v1.x.

# 31. Exercise family / variation graph

Potential:

```json
"relationships": {
  "family": "bench_press",
  "variantOf": "Barbell_Bench_Press_-_Medium_Grip",
  "similarTo": []
}
```

Use cases:

- substitutions;
- search;
- equipment migration;
- research grouping;
- interop.

Do not add similarity scores without a methodology.

# 32. Fine-grained anatomy

Do not replace the stable broad muscle ontology.

Add an optional secondary layer.

Example:

```json
"anatomy": {
  "direct": [
    "pectoralis_major_sternal",
    "pectoralis_major_clavicular"
  ]
}
```

Potential subdivisions:

- anterior/lateral/posterior deltoid;
- upper/middle/lower trapezius;
- rectus femoris/vasti;
- individual hamstrings;
- gastrocnemius/soleus;
- glute max/med/min;
- individual rotator cuff muscles.

Broad groups remain the stable analytics interface.

# 33. Evidence metadata improvements

Potential additive fields:

```json
{
  "studyType": "systematic_review",
  "evidenceDomain": "hypertrophy",
  "population": "trained_adults",
  "measurement": ["ultrasound"],
  "supports": ["direct_role"]
}
```

Possible domains:

```text
hypertrophy
strength
emg
kinematics
kinetics
biomechanics
training_intervention
```

Avoid numerical evidence scores unless a defensible methodology is defined.

# 34. Citation and research reproducibility

Add:

```text
CITATION.cff
```

Optionally connect GitHub releases to Zenodo for versioned DOIs.

Potential paper/preprint:

> Free Exercise DB++: An Evidence-Audited Exercise Vocabulary and Resistance-Training Interchange Framework

# 35. Community contribution model

Add:

```text
CONTRIBUTING.md
.github/ISSUE_TEMPLATE/
```

Templates:

1. mapping correction;
2. evidence correction/addition;
3. new upstream exercise;
4. taxonomy proposal;
5. workout schema proposal;
6. interop mapping issue.

Scientific mapping changes should include rationale and citations.

# 36. Upstream automation

Evolve weekly CI into a watcher.

On upstream changes:

- added IDs -> review queue;
- removed IDs -> hard compatibility alert;
- changed records -> diff report;
- no change -> no noisy commit.

Do not auto-release upstream changes.

# 37. Release artifacts

Every DB++ release should publish:

```text
free-exercise-db-plusplus.json
free-exercise-db-plusplus.schema.json
workout.schema.json
SHA256SUMS
METHODOLOGY.md
COMPATIBILITY.md
EVIDENCE.md
```

When workout schema reaches 1.0, optionally add:

```text
workout-examples.zip
interop-mappings.zip
```

# 38. CI roadmap

Existing:

- DB generation;
- schema validation;
- evidence invariants;
- reproducibility;
- golden mappings;
- confidence policy.

Add next:

### Workout

```text
validate workout schema
validate all valid examples
reject all invalid fixtures
migration tests
```

### Interop

```text
validate mapping JSON schema
all mapping references resolve
detect duplicate ambiguous external-code mappings
validate FHIR examples
```

### Consumer libraries

```text
Python tests
Swift package tests
decode exact release artifacts
```

# 39. Analytics reference implementation

After workout schema stabilizes, add:

```text
src/analysis/
```

Reference calculations:

- direct sets;
- indirect sets;
- effective sets;
- weekly effective sets;
- reps per muscle;
- tonnage;
- frequency;
- estimated 1RM;
- RPE/RIR trends.

Reference effective-set policy:

```text
For each completed, volume-eligible counted set:
    direct muscle   += 1.0
    indirect muscle += 0.5
    stabilizer      += 0.0
```

Do not bake warmup/failure/technique-set analytics policy into the interchange schema.

# 40. Set-credit model policy

Keep the project default:

```text
direct     = 1.0
indirect   = 0.5
stabilizer = 0.0
```

Do not reintroduce multiple competing models into the database.

Applications may compute alternatives independently.

# 41. Workout schema questions to settle before 1.0

Create ADRs/issues for:

1. structured tempo vs string;
2. `segments` semantics;
3. superset/circuit grouping;
4. laterality overrides;
5. custom exercise representation;
6. extension namespace rules;
7. rep telemetry vocabulary;
8. bodyweight/load/assistance model;
9. band and machine resistance;
10. partial/incomplete sets;
11. unknown/missing values;
12. timezone policy;
13. UCUM strictness.

# 42. ADRs

Add:

```text
docs/adr/
```

Suggested:

```text
0001-single-self-contained-db-json.md
0002-direct-indirect-set-credit-model.md
0003-workout-schema-separate-from-exercise-db.md
0004-ucum-compatible-units.md
0005-external-interop-via-mapping-layers.md
0006-workout-extension-namespaces.md
```

# Part II — Workout PLAN, TARGET, and PLAN↔ACTUAL Analysis

This section is now the **authoritative next workstream**. It supersedes the older immediate-sprint ordering later in the original roadmap because the repository has already implemented Workout ACTUAL schema 0.2 and substantial interop scaffolding.

## Domain model and terminology

Use these terms deliberately and consistently:

```text
EXERCISE
= relatively static definition from Free Exercise DB++

PLAN
= prescribed/intended training

ACTUAL
= observed/performed training

TARGET
= desired analytical target or acceptable range

ANALYSIS
= derived comparison or summary
```

The architecture is:

```text
                            TARGET
                      volume-target.schema.json
                              |
                              v
EXERCISE DEFINITIONS -> PLAN -> ACTUAL -> ANALYSIS
free-exercise-db++     plan     workout    derived output
                           \       /
                            \     /
                             v   v
                        INTEROPERABILITY
                    FIT / HealthKit / FHIR / etc.
```

Do not overload one schema to represent all of these concerns.

## Why PLAN must remain separate from ACTUAL

`workout.schema.json` is an observation format. It stores what happened.

PLAN stores a prescription, which commonly contains ranges and intentions rather than observations:

```text
4 sets
6–8 reps
70–75% 1RM
RPE 7–8
RIR 2–3
```

ACTUAL stores measurements:

```text
100 kg × 8 @ RPE 8
100 kg × 8 @ RPE 8.5
100 kg × 7 @ RPE 9
set 4 skipped
```

Using the same semantics for both creates ambiguity around skipped work, ranges, substitutions, progression, plan revisions, and adherence. Therefore add a separate public artifact:

```text
workout-plan.schema.json
```

Keep `workout.schema.json` as ACTUAL.

## Artifact family

The intended public artifact family becomes:

```text
free-exercise-db-plusplus.json
free-exercise-db-plusplus.schema.json
workout.schema.json
workout-plan.schema.json
volume-target.schema.json
interop-mapping.schema.json
mappings/*
```

Derived analytical reports are not authoritative inputs and should not be embedded back into PLAN or ACTUAL files.

## PLAN hierarchy

Recommended hierarchy:

```text
WorkoutPlan
  ├── planId
  ├── revisionId
  ├── name
  ├── description
  ├── provenance
  └── phases[] / cycle
       └── plannedSessions[]
            └── exercisePrescriptions[]
                 └── setPrescription or plannedSets[]
```

Conceptually:

```text
Plan
  ↓
Phase
  ↓
Cycle / microcycle
  ↓
Planned session
  ↓
Exercise prescription
  ↓
Set prescription
```

## Never assume a calendar week

Programs may use:

```text
7-day cycles
8-day rotations
10-day microcycles
3-on / 1-off
A/B alternate-day schedules
research protocols with arbitrary periods
```

PLAN should store its native cycle explicitly:

```json
{
  "cycle": {
    "lengthDays": 8
  }
}
```

Analysis may normalize to seven days:

```text
weeklyEquivalent = nativeCycleVolume × 7 / cycleLengthDays
```

but must report both native and normalized periods. Never silently normalize.

Example analysis metadata:

```json
{
  "nativePeriodDays": 8,
  "nativeEffectiveSets": 16,
  "normalizedPeriodDays": 7,
  "normalizedEffectiveSets": 14
}
```

## Plan identity and immutable revisioning

Use both:

```text
planId
revisionId
```

Example:

```json
{
  "planId": "study-arm-a",
  "revisionId": "study-arm-a-r3"
}
```

`planId` identifies the conceptual plan. `revisionId` identifies the exact prescription version.

Once ACTUAL workouts reference a plan revision, do not mutate that revision in place. Historical analysis must always be able to recover the prescription actually in force.

Trainer example:

```text
client-hypertrophy
  r1
  r2
  r3
```

Research example:

```text
intervention-arm-a
  protocol-v1
  protocol-v2-amendment
```

## Planned session identity

Each planned session gets a stable identifier:

```json
{
  "planSessionId": "upper-a"
}
```

or:

```json
{
  "planSessionId": "week-03-day-02"
}
```

An ACTUAL session can then include an optional link:

```json
{
  "planReference": {
    "planId": "upper-lower",
    "revisionId": "r2",
    "planSessionId": "upper-a"
  }
}
```

## Exercise prescription identity

Each planned occurrence needs its own stable `prescriptionId` because the same `exerciseId` can appear multiple times.

```json
{
  "prescriptionId": "upper-a-bench-01",
  "exerciseId": "Barbell_Bench_Press_-_Medium_Grip"
}
```

ACTUAL exercise observations may later reference:

```json
{
  "exercisePrescriptionId": "upper-a-bench-01"
}
```

## Set prescription identity

For exact heterogeneous set plans, optionally allow `setPrescriptionId`.

Do not require it for common homogeneous prescriptions such as `4 × 8–12`.

Support both:

1. aggregate repeated-set prescription;
2. explicit planned set list.

Recommended rule before PLAN schema 1.0:

- `setPrescription` for homogeneous repeated sets;
- `plannedSets` for heterogeneous prescriptions;
- exactly one of them on a given exercise prescription.

## Planned ranges

Plans frequently prescribe ranges rather than exact values. Use a reusable range concept:

```json
{
  "min": 3,
  "target": 4,
  "max": 5
}
```

Examples:

```json
{
  "reps": {
    "min": 8,
    "target": 10,
    "max": 12
  }
}
```

```json
{
  "rir": {
    "min": 1,
    "target": 2,
    "max": 3
  }
}
```

Do not require `target` when only a min/max range is known.

## PLAN set prescription model

Example aggregate prescription:

```json
{
  "prescriptionId": "upper-a-bench",
  "exerciseId": "Barbell_Bench_Press_-_Medium_Grip",
  "sets": {
    "count": {
      "min": 4,
      "target": 4,
      "max": 4
    },
    "reps": {
      "min": 6,
      "target": 8,
      "max": 8
    },
    "effort": {
      "rir": {
        "min": 1,
        "target": 2,
        "max": 2
      }
    }
  }
}
```

Example heterogeneous explicit sets:

```json
{
  "plannedSets": [
    {
      "setPrescriptionId": "s1",
      "setType": "working",
      "reps": {"target": 8}
    },
    {
      "setPrescriptionId": "s2",
      "setType": "working",
      "reps": {"target": 6}
    }
  ]
}
```

## PLAN phases and periodization

Plans must eventually support periodization:

```text
Plan
  └── phases[]
```

Example:

```json
{
  "phases": [
    {
      "phaseId": "accumulation",
      "durationCycles": 3,
      "cycle": {}
    },
    {
      "phaseId": "deload",
      "durationCycles": 1,
      "cycle": {}
    }
  ]
}
```

Analysis should return phase-specific and cycle-specific volume, average across a phase, average across a whole plan, and min/max volume over time. Do not collapse periodized plans to a single misleading weekly number.

## Progression prescriptions

Progression should eventually be first-class metadata but should not become arbitrary executable scripting.

Potential controlled types:

```text
fixed
linear_load
linear_reps
double_progression
percentage_1rm
rpe_based
rir_based
autoregulated
custom
```

For early PLAN 0.x, descriptive progression metadata is sufficient.

## ACTUAL linkage

The next ACTUAL schema version should add optional planning references:

Session:

```json
{
  "planReference": {
    "planId": "upper-lower",
    "revisionId": "r2",
    "planSessionId": "upper-a"
  }
}
```

Exercise:

```json
{
  "exercisePrescriptionId": "upper-a-bench"
}
```

Set:

```json
{
  "setPrescriptionId": "upper-a-bench-s3"
}
```

All references remain optional so ACTUAL workouts are independently useful.

## Exercise substitutions

Substitutions are first-class, not inferred away.

Plan:

```text
Barbell back squat
```

ACTUAL:

```text
Hack squat
```

Represent:

```json
{
  "exerciseId": "Hack_Squat",
  "exercisePrescriptionId": "lower-a-back-squat",
  "substitution": {
    "plannedExerciseId": "Barbell_Back_Squat",
    "reason": "equipment_unavailable"
  }
}
```

Potential reasons:

```text
equipment_unavailable
pain_or_discomfort
coach_decision
athlete_preference
fatigue
time_constraint
progression
regression
research_protocol_deviation
other
unknown
```

## Two adherence concepts

Do not collapse adherence into one opaque score.

### Prescription adherence

Did the athlete perform what was prescribed?

```text
Back squat planned
Hack squat performed
strict exercise adherence = false
```

### Muscle-volume coverage adherence

Did ACTUAL work provide the DB++ muscle-set coverage intended by PLAN?

```text
planned quads = 4 effective sets
actual quads  = 4 effective sets
quad coverage adherence = 100%
```

This is **not** a claim of physiological equivalence. Use the term `muscle-volume coverage`, not `physiological equivalence`.

## Adherence dimensions

Expose separate components:

- session adherence;
- exact exercise-prescription adherence;
- substitution-adjusted exercise completion;
- set adherence;
- rep adherence;
- load adherence where meaningful;
- RPE/RIR adherence;
- volume-load adherence where meaningful;
- direct-set adherence by muscle;
- indirect-set adherence by muscle;
- effective-set adherence by muscle;
- movement-pattern coverage adherence.

Session adherence:

```text
completed planned sessions / scheduled planned sessions
```

Set adherence:

```text
completed planned sets / planned sets
```

For ranged prescriptions calculate relative to minimum, target, and maximum rather than pretending one exact denominator exists.

## DB++ set-credit calculation

The default integration remains exactly:

```text
direct muscle     +1.0 per counted set
indirect muscle   +0.5 per counted set
stabilizer        +0.0 effective sets
```

Always preserve components:

```json
{
  "directSets": 10,
  "indirectSets": 4,
  "stabilizerSets": 2,
  "effectiveSets": 12
}
```

Never report only the effective total when the underlying components are available.

## Counting policy belongs in analysis, not schema

PLAN and ACTUAL store prescriptions and observations. The analysis layer decides which sets count.

A possible named policy:

```json
{
  "policyId": "dbpp-default-volume-v1",
  "countSetTypes": ["working", "backoff", "drop", "amrap"],
  "requireCompleted": true,
  "segmentPolicy": "parent_set_once"
}
```

Do not make warmup/technique/failure rules implicit physiological truths in the interchange schema.

## Drop, cluster, and rest-pause counting

ACTUAL 0.2 already supports macro-segments.

Recommended default DB++ set accounting:

> One completed parent set contributes one set credit regardless of the number of drop/rest-pause/cluster segments.

Alternative analytical policies may exist outside the database, but do not automatically count each segment as a full set.

## Unilateral counting

Resolve by ADR before analysis 1.0.

Recommended broad subject-level default:

> A single set recorded as bilateral/alternating or “each side” counts as one exercise set. If left and right are explicitly recorded as separate sets, retain those observations but avoid accidental double counting when the analysis question is subject-level rather than limb-level volume.

## Canonical coverage result

A PLAN coverage result should look conceptually like:

```json
{
  "period": {
    "nativeDays": 8,
    "normalizedDays": 7
  },
  "muscles": {
    "chest": {
      "directSets": 10,
      "indirectSets": 4,
      "stabilizerSets": 2,
      "effectiveSets": 12
    }
  },
  "patterns": {
    "horizontal_push": {
      "sets": 10
    }
  }
}
```

For ranged plans:

```json
{
  "effectiveSets": {
    "min": 10,
    "target": 12,
    "max": 14
  }
}
```

## Movement-pattern coverage

The analyzer should also answer movement-pattern questions using DB++ canonical patterns:

```text
horizontal push
vertical push
horizontal pull
vertical pull
squat
hinge
trunk flexion
rotation
loaded carry
...
```

This is important for coaches and for comparing protocols even where muscle-group totals alone are insufficient.

## TARGET artifact

Add:

```text
volume-target.schema.json
```

TARGET remains separate from PLAN because one plan can be evaluated against different goals.

Example:

```json
{
  "schemaVersion": "0.1.0",
  "targetId": "example-hypertrophy",
  "periodDays": 7,
  "muscles": {
    "chest": {
      "minimum": 10,
      "target": 14,
      "maximum": 18
    },
    "lats": {
      "minimum": 10,
      "target": 14,
      "maximum": 18
    }
  }
}
```

## Target semantics

Allow:

```text
minimum
target
maximum
```

At least one should exist per targeted muscle.

Support min-only, max-only, range-only, and target-centered profiles.

Do not present a bundled target profile as universally scientifically optimal unless its provenance explicitly supports such a claim.

## Target provenance

Recommended:

```json
{
  "source": {
    "type": "coach_defined",
    "citation": null,
    "notes": "Client-specific hypertrophy target."
  }
}
```

Possible types:

```text
coach_defined
research_protocol
literature_derived
organization_guideline
user_defined
software_default
other
```

## Target gap statuses

Recommended:

```text
below_minimum
within_range_below_target
at_target
within_range_above_target
above_maximum
not_targeted
```

Example:

```json
{
  "muscle": "chest",
  "effectiveSets": 12,
  "minimum": 10,
  "target": 14,
  "maximum": 18,
  "differenceFromTarget": -2,
  "status": "within_range_below_target"
}
```

## PLAN vs TARGET API

Reference Python API:

```python
compare_to_targets(plan, target_profile, db)
```

Return:

```text
muscle
direct_sets
indirect_sets
effective_sets
minimum
target
maximum
difference_from_target
status
```

## PLAN vs PLAN API

Reference API:

```python
compare_plans(plan_a, plan_b, db)
```

Compare:

- direct sets;
- indirect sets;
- effective sets;
- movement patterns;
- session frequency;
- muscle exposure frequency;
- exercise frequency.

Return absolute deltas and optional relative percentage differences where denominators are nonzero.

## PLAN vs ACTUAL API

Reference API:

```python
compare_plan_actual(plan, actual_workouts, db)
```

Return at minimum:

```text
session adherence
exercise adherence
set adherence
rep adherence
load adherence when meaningful
RPE/RIR adherence
volume-load adherence when meaningful
muscle direct-set adherence
muscle indirect-set adherence
muscle effective-set adherence
pattern coverage adherence
substitution report
missing-work report
unplanned-work report
```

## Unplanned ACTUAL work

Do not discard work not found in the plan.

Classify actual observations as:

```text
planned_matched
substitution
unplanned_addition
unable_to_match
```

Unplanned additions still contribute to ACTUAL muscle coverage.

A report should distinguish planned actual coverage, extra actual coverage, and total actual coverage.

## Missing planned work

Do not create synthetic ACTUAL sets. Missing planned work is derived analysis output.

Example:

```json
{
  "prescriptionId": "upper-a-row",
  "status": "not_performed"
}
```

## Matching algorithm

Preferred order:

1. explicit `exercisePrescriptionId`;
2. explicit `setPrescriptionId`;
3. exact plan-session reference plus exact `exerciseId`;
4. explicit substitution record;
5. deterministic positional matching only when unambiguous;
6. otherwise `unable_to_match`.

Do not use fuzzy natural-language matching by default.

## Volume-load adherence

Where load units are compatible:

```text
volumeLoad = Σ(reps × load)
```

Only compute when resistance is meaningfully mass-like and units can be normalized.

Do not compare machine levels, band labels, and kilograms as if they were equivalent.

For bodyweight-plus-load, preserve external added load separately unless body mass is explicitly available.

## Planned intensity prescriptions

PLAN should eventually support:

```text
absolute load
%1RM
RPE/RIR
velocity target
machine setting
bodyweight plus load
assistance
```

Example:

```json
{
  "intensity": {
    "percent1RM": {
      "min": 70,
      "target": 75,
      "max": 80
    }
  }
}
```

Do not require conversion to kilograms.

## PLAN frequency analytics

Calculate:

```text
sessions per native cycle
sessions per 7 days
muscle exposure frequency
movement-pattern frequency
exercise frequency
```

Define a muscle exposure as at least one counted set for that muscle in a session.

## Periodized analytics

For phased plans, expose time series:

```text
cycle/week
muscle
direct sets
indirect sets
effective sets
```

Then derive:

```text
peak volume
minimum volume
average volume
deload reduction
```

Do not infer whether a progression is optimal.

## Research-oriented tidy exports

PLAN coverage table:

```text
plan_id
revision_id
phase_id
cycle_index
muscle
planned_direct_sets
planned_indirect_sets
planned_effective_sets
```

PLAN vs ACTUAL table:

```text
subject_id
plan_id
revision_id
period
muscle
planned_direct_sets
actual_direct_sets
planned_indirect_sets
actual_indirect_sets
planned_effective_sets
actual_effective_sets
adherence_pct
```

Exercise adherence table:

```text
subject_id
session_id
plan_session_id
prescription_id
planned_exercise_id
actual_exercise_id
match_type
planned_sets
actual_sets
```

CSV should be first-class. Parquet can be added later without becoming part of the interchange contract.

## Trainer-oriented summary output

The analysis engine should emit JSON that presentation layers can render like:

```text
Client: X
Period: Aug 17–23

Chest:
  Planned 12.0
  Actual  11.0
  Adherence 91.7%

Lats:
  Planned 14.0
  Actual   9.0
  Adherence 64.3%

Substitutions:
  Back Squat -> Hack Squat

Skipped:
  Upper B cable row, 3 sets

Extra:
  Lateral raise, 4 sets
```

Keep presentation out of core analysis semantics.

## Analysis package layout

Add:

```text
src/analysis/
    __init__.py
    coverage.py
    plan_volume.py
    plan_compare.py
    plan_actual.py
    targets.py
    matching.py
    units.py
    policies.py
    export.py
```

Responsibilities:

- `coverage.py`: DB++ exercise -> muscle/pattern credit expansion;
- `plan_volume.py`: prescription ranges -> coverage ranges;
- `plan_compare.py`: PLAN A vs PLAN B;
- `plan_actual.py`: adherence and coverage comparison;
- `targets.py`: target gaps;
- `matching.py`: prescription↔actual matching;
- `units.py`: safe compatible unit normalization;
- `policies.py`: explicit counted-set policies;
- `export.py`: JSON/CSV research output.

## Public Python API direction

```python
from fedbpp import Database
from fedbpp.plan import WorkoutPlan, VolumeTarget
from fedbpp.workout import Workout
from fedbpp.analysis import (
    analyze_plan,
    compare_plans,
    compare_to_targets,
    compare_plan_actual,
)
```

Example:

```python
db = Database.load("free-exercise-db-plusplus.json")
plan = WorkoutPlan.load("plan.json")
actuals = Workout.load_many("client/*.json")
targets = VolumeTarget.load("targets.json")

coverage = analyze_plan(plan, db)
gaps = compare_to_targets(plan, targets, db)
adherence = compare_plan_actual(plan, actuals, db)
```

Python should define the executable reference semantics before Swift analysis parity is required.

## Swift direction

Eventually expose equivalent semantics:

```swift
let db = try FEDatabase.load(url: dbURL)
let plan = try WorkoutPlan.load(url: planURL)
let actuals = try Workout.loadMany(urls: workoutURLs)

let report = try PlanActualAnalyzer.compare(
    plan: plan,
    actuals: actuals,
    database: db
)
```

Use the same JSON fixtures in Python and Swift tests.

## PLAN schema files and examples

Add:

```text
workout-plan.schema.json
volume-target.schema.json

docs/WORKOUT-PLAN.md
docs/PLAN-ANALYSIS.md
docs/VOLUME-TARGETS.md

examples/plans/
    basic-upper-lower.json
    push-pull-legs.json
    eight-day-rotation.json
    four-week-periodized.json
    research-protocol.json
    ranged-prescription.json

examples/targets/
    example-hypertrophy.json
    client-specific.json
    study-protocol.json

fixtures/plan/invalid/
fixtures/target/invalid/
```

## PLAN schema version path

```text
0.1  basic cycle + session + exercise prescriptions
0.2  phases + revisions + explicit planned sets + richer intensity
0.3  progression metadata and advanced prescriptions
0.9  release candidate
1.0  stable PLAN interchange contract
```

TARGET may reach 1.0 earlier because it is intentionally small.

## PLAN 0.1 scope

Implement first:

- `planId`;
- `revisionId`;
- name/description;
- provenance;
- cycle length days;
- planned sessions;
- `planSessionId`;
- relative day offset;
- exercise prescriptions;
- `prescriptionId`;
- DB++ `exerciseId` or custom exercise fallback;
- exact/ranged set count;
- exact/ranged reps;
- optional load;
- optional RPE/RIR;
- notes.

Do not add executable progression scripting in 0.1.

## TARGET 0.1 scope

Implement:

- `targetId`;
- `periodDays`;
- muscle target map;
- minimum/target/maximum;
- provenance;
- notes.

Later add movement-pattern targets.

## Analysis metadata and reproducibility

Every result should identify:

```text
DB schema version
converter version
PLAN schema version
ACTUAL schema version(s)
TARGET schema version if used
analysis library version
set-credit policy
counting policy
period normalization
```

Example:

```json
{
  "analysisMetadata": {
    "setCreditPolicy": "dbpp-default",
    "directCredit": 1.0,
    "indirectCredit": 0.5,
    "stabilizerCredit": 0.0,
    "normalizedPeriodDays": 7
  }
}
```

This is essential for research reproducibility.

## Custom/unmapped exercises

PLAN and ACTUAL may contain custom exercises.

Behavior:

```text
known DB++ exercise -> normal coverage
custom/unmapped exercise -> retain record, coverage unknown
```

Do not infer muscle roles from free text.

Analysis output should list unmapped prescriptions/observations and coverage completeness:

```json
{
  "coverageCompleteness": {
    "plannedSets": 50,
    "mappedSets": 47,
    "unmappedSets": 3,
    "mappedFraction": 0.94
  }
}
```

## Confidence-aware diagnostics

Default set credits do not change based on DB++ confidence.

Optional diagnostic breakdown may report:

```json
{
  "effectiveSets": 12,
  "confidenceBreakdown": {
    "high": 10,
    "medium": 2
  }
}
```

Do not discount medium-confidence mappings automatically.

## Evidence-aware traceability

Optional detailed contribution trace:

```json
{
  "exerciseId": "...",
  "sets": 4,
  "muscle": "chest",
  "role": "direct",
  "credit": 4.0,
  "evidenceRefs": ["pattern:horizontal_push"]
}
```

Useful for research audits, but not required in compact reports.

## Research cohort use cases

The architecture should support intervention studies with:

```text
prescribed weekly sets per muscle
actual weekly sets per muscle
participant adherence
protocol deviations
exercise substitutions
planned vs actual RPE
planned vs actual load
planned vs actual volume-load
```

Later cohort aggregation may expose descriptive statistics, but statistical inference should remain in external R/Python workflows initially.

## Date windows

ACTUAL comparison should support explicit windows:

```text
calendar week
rolling 7 days
native plan cycle
study week
phase
custom date range
```

Avoid ambiguous `week` assumptions.

## Privacy

PLAN and ACTUAL schemas should use opaque athlete/subject IDs and should not require names, email, DOB, or device serial numbers.

## ADRs to add

```text
docs/adr/0007-plan-vs-actual-separation.md
docs/adr/0008-plan-cycle-not-calendar-week.md
docs/adr/0009-plan-revision-immutability.md
docs/adr/0010-muscle-volume-coverage-analysis.md
docs/adr/0011-set-counting-policy.md
docs/adr/0012-substitution-semantics.md
docs/adr/0013-targets-separate-from-plans.md
docs/adr/0014-plan-actual-explicit-linking.md
```

## PLAN and interop relationship

Interop mappings should eventually identify their source artifact explicitly:

```text
exercise-db
workout-actual
workout-plan
```

FHIR is likely the strongest PLAN interop candidate because healthcare standards conceptually distinguish intentions/plans from observations.

Garmin FIT, HealthKit, and Health Connect are generally more ACTUAL/device-oriented; document PLAN capabilities separately and preserve DB++ PLAN as the high-fidelity source of truth when targets are lossy.

Do not implement exporters before the PLAN/ACTUAL semantics are stable enough to map deliberately.


# Part III — Authoritative execution sequence from current `main`

The repository already contains Workout ACTUAL 0.2, workout migration support, `docs/WORKOUT-INTERCHANGE.md`, interop documentation, `interop-mapping.schema.json`, and mapping/package scaffolding. Therefore the earlier roadmap instruction to “implement Workout 0.2 next” is complete and must not be repeated.

## Release sequence

Recommended project sequence from the current state:

```text
v1.1
  Workout PLAN schema 0.1
  Volume TARGET schema 0.1
  PLAN coverage analysis
  TARGET gap analysis
  PLAN-vs-PLAN comparison

v1.2
  Workout ACTUAL schema 0.3
  PLAN references
  substitution metadata
  PLAN-vs-ACTUAL matching/adherence

v1.3
  PLAN phases / periodization
  explicit planned sets
  research tidy exports
  analysis policy stabilization

v1.4
  PLAN/ACTUAL interop mapping refinement
  FHIR / FIT / HealthKit / Health Connect

v1.5
  Python package stabilization
  Swift parity

v1.6+
  exercise families
  richer taxonomy
  fine-grained anatomy
  richer evidence metadata
```

## Sprint 1 — Workout PLAN 0.1

Deliver:

```text
workout-plan.schema.json
docs/WORKOUT-PLAN.md
examples/plans/basic-upper-lower.json
examples/plans/eight-day-rotation.json
examples/plans/ranged-prescription.json
examples/plans/research-protocol.json
fixtures/plan/invalid/*
tests/plan/test_schema.py
tests/plan/test_examples.py
src/plan/validate_plan.py
```

Guardrails:

- do not modify the stable exercise DB contract;
- do not redesign ACTUAL 0.2 in this sprint;
- do not copy DB++ muscle mappings into PLAN files;
- do not store derived muscle totals in PLAN files;
- do not implement FHIR/FIT/HealthKit exporters yet.

### Codex prompt — Sprint 1

```text
Read ROADMAP.md and the current Free Exercise DB++ repository.

Implement Workout PLAN schema 0.1.

The existing workout.schema.json 0.2.0 represents ACTUAL/performed observations and must remain unchanged in this sprint.

Create a separate workout-plan.schema.json for prescriptions.

Requirements:
- planId and revisionId
- name/description/provenance
- arbitrary cycle length in days
- planned sessions with stable planSessionId
- relative day offset
- exercise prescriptions with stable prescriptionId
- DB++ exerciseId plus custom exercise fallback
- exact or ranged set count
- exact or ranged reps
- optional load prescription
- optional RPE/RIR prescription
- notes
- deterministic validation
- realistic examples including a 7-day plan, 8-day rotation, ranged prescription, and research protocol
- deliberately invalid fixtures
- tests
- docs/WORKOUT-PLAN.md

Do not:
- duplicate DB++ muscle roles into plan files
- calculate/store weekly muscle coverage in the plan
- modify direct/indirect/stabilizer semantics
- modify the 1.0/0.5/0.0 DB++ set-credit model
- merge PLAN and ACTUAL schemas
- add PLAN-vs-ACTUAL linking yet
- add external interop code yet

Run all existing tests plus the new plan tests before finishing.
```

## Sprint 2 — TARGET 0.1 + PLAN coverage

Deliver:

```text
volume-target.schema.json
docs/VOLUME-TARGETS.md
examples/targets/*
fixtures/target/invalid/*
src/analysis/coverage.py
src/analysis/plan_volume.py
src/analysis/targets.py
tests/analysis/*
tests/target/*
```

Required APIs:

```python
analyze_plan(plan, db)
compare_to_targets(plan, target_profile, db)
```

Required results:

```text
direct sets
indirect sets
stabilizer participation sets
effective sets
movement-pattern sets
native-cycle totals
explicit 7-day normalized totals
coverage completeness
```

Golden-test all calculations by hand.

### Codex prompt — Sprint 2

```text
Read ROADMAP.md and the repository after Workout PLAN schema 0.1 is green.

Implement Volume TARGET schema 0.1 and the reference PLAN coverage analyzer.

Use the DB++ metadata setCredits exactly:
direct=1.0
indirect=0.5
stabilizer=0.0

Preserve direct, indirect, stabilizer, and effective-set totals separately.
Normalize arbitrary plan cycles to seven days only as an explicitly reported derived view, while retaining native-cycle totals.
Report unmapped exercise coverage completeness.
Implement target minimum/target/maximum gap states.

Do not implement PLAN-vs-ACTUAL yet.
```

## Sprint 3 — PLAN-vs-PLAN

Implement:

```python
compare_plans(plan_a, plan_b, db)
```

Compare muscles, direct/indirect/effective sets, movement patterns, and frequencies. Add deterministic JSON and tidy CSV output.

## Sprint 4 — ACTUAL schema 0.3 PLAN linkage

Compatibly add:

```text
planReference
exercisePrescriptionId
setPrescriptionId
substitution
```

Add deterministic migration `0.2 -> 0.3`.

All linkage fields are optional. Standalone ACTUAL workouts remain valid.

## Sprint 5 — PLAN vs ACTUAL

Deliver:

```text
src/analysis/matching.py
src/analysis/plan_actual.py
```

Implement explicit-reference-first matching and report:

```text
matched
substitution
unplanned_addition
missing_prescription
unable_to_match
```

Then calculate session, exercise, set, muscle, and pattern adherence.

No fuzzy matching by default.

## Sprint 6 — PLAN 0.2 phases and periodization

Add:

- phases;
- duration cycles;
- explicit planned sets;
- setPrescriptionId;
- optional/conditional prescriptions if justified;
- progression metadata;
- richer intensity prescriptions.

Update analysis for time-varying volume.

## Sprint 7 — Research export

Add deterministic tidy CSV export for PLAN coverage and PLAN-vs-ACTUAL adherence. Later add Parquet only as a convenience format, not as an interchange requirement.

## Sprint 8 — PLAN-aware interoperability

Update mapping architecture to distinguish:

```text
exercise-db
workout-actual
workout-plan
```

Document mappings first. FHIR should be the first serious PLAN mapping candidate. Continue FIT/HealthKit/Health Connect mainly as ACTUAL-oriented adapters unless their current APIs support prescription semantics adequately.

## Sprint 9 — Consumer libraries

Stabilize Python reference package, then implement Swift parity against the same fixtures.

## Deferred taxonomy work

After PLAN/ACTUAL/TARGET/ANALYSIS is stable, continue:

- exercise families and variants;
- laterality/kinetic-chain metadata in definitions where useful;
- movement planes and joint actions;
- aliases/search names;
- fine-grained anatomy;
- richer evidence metadata.

Do not let this delay the plan-analysis workstream.

# Non-goals

Near-term non-goals:

- one overloaded PLAN+ACTUAL schema;
- precomputed muscle coverage stored inside plans as authoritative data;
- universal “optimal” set targets;
- physiological-equivalence claims for substitutions;
- silent fuzzy matching;
- alternate competing core set-credit models;
- RPE/RIR-weighted default effective-set credits;
- automatic full-set credit for every drop/rest-pause segment;
- native FHIR/FIT/HealthKit fields embedded in core schemas;
- mandatory seven-day cycles;
- mutation of historical plan revisions;
- required personally identifying athlete data;
- pandas/Parquet as mandatory dependencies.

# Definition of success

The next major project milestone is reached when:

1. a trainer can encode a realistic PLAN;
2. a research protocol can encode prescribed resistance training;
3. a plan can use a 7-day or non-7-day cycle;
4. DB++ deterministically calculates direct/indirect/effective sets per muscle;
5. movement-pattern coverage is available;
6. a plan can be compared against arbitrary TARGET profiles;
7. Plan A and Plan B can be compared;
8. ACTUAL sessions can link to exact plan revisions and prescriptions;
9. substitutions preserve intended and performed identities;
10. strict prescription adherence and muscle-volume coverage adherence are both available;
11. skipped and unplanned work remain visible;
12. tidy research exports are deterministic;
13. Python and Swift eventually pass the same fixtures;
14. at least one external standard has a documented PLAN mapping and at least one has a validated ACTUAL export.

# Long-term vision

Free Exercise DB++ becomes a small, independently versioned ecosystem:

```text
EXERCISE VOCABULARY
  stable exercise identity + evidence-audited muscle roles

WORKOUT PLAN
  what was prescribed

WORKOUT ACTUAL
  what was performed

TARGET
  what coverage is desired

ANALYSIS
  what the plan provides,
  where the gaps are,
  how Plan A differs from Plan B,
  and how actual training differed from prescription

INTEROP
  translation to fitness, health, and research ecosystems
```

The project’s strongest long-term value is the combination of stable exercise identity, evidence-audited muscle roles, portable prescriptions, portable observations, deterministic muscle-volume analysis, explicit adherence semantics, and documented external interoperability.
