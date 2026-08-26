# Free Exercise DB++

Free Exercise DB++ is a self-contained, evidence-audited annotation layer over
[yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db).

It preserves every upstream exercise record and adds normalized movement classification,
muscle-role annotations, resistance-volume eligibility, confidence, and embedded evidence
provenance for training apps, coaches, researchers, and fitness software.

## Download

**Database:**  
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/free-exercise-db-plusplus.json

**Database JSON Schema:**  
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/free-exercise-db-plusplus.schema.json

**Exercise relationships:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/exercise-relationships.json

**Exercise relationship schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/exercise-relationships.schema.json

**Workout interchange schema:**  
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/workout.schema.json

**Workout PLAN schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/workout-plan.schema.json

**Volume TARGET schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/volume-target.schema.json

**TrainingProfile schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/training-profile.schema.json

**CoachDecision schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/coach-decision.schema.json

**WorkoutIntent schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/workout-intent.schema.json

**Interop mapping schema:**
https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/interop-mapping.schema.json

**Versioned releases:**  
https://github.com/johnarleyburns/free-exercise-db-plusplus/releases

Consumers need only `free-exercise-db-plusplus.json` at runtime. The schemas are optional
validation tools; evidence provenance is embedded directly in the database.

## What DB++ adds

Each exercise preserves the complete upstream record under `source` and adds:

- training type, modality, sport context, and competition-movement classification;
- canonical movement patterns;
- `direct`, `indirect`, and `stabilizers` muscle roles;
- `volumeEligible`;
- mapping confidence and review reasons;
- evidence references.

DB++ uses one effective-set convention:

| Muscle role | Set credit |
|---|---:|
| Direct | 1.0 |
| Indirect | 0.5 |
| Stabilizer | 0.0 |

These are analytical credits for volume accounting, not a claim that hypertrophy or fatigue
is literally linear. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Quick start

Download the current database:

```bash
curl -L   https://raw.githubusercontent.com/johnarleyburns/free-exercise-db-plusplus/main/free-exercise-db-plusplus.json   -o free-exercise-db-plusplus.json
```

### Python

```python
import json

with open("free-exercise-db-plusplus.json", encoding="utf-8") as f:
    db = json.load(f)

bench = db["exercises"]["Barbell_Bench_Press_-_Medium_Grip"]

print(bench["annotation"]["direct"])
print(bench["annotation"]["indirect"])
print(db["metadata"]["setCredits"])
```

The public fedbpp package provides runnable examples under [examples/python](examples/python/): load a DB++ database and PLAN, calculate effective muscle sets, compare a PLAN with a TARGET, compare PLAN vs ACTUAL, and compare two PLANs. Analysis uses dbpp-default-volume-v1 and reads direct/indirect/stabilizer credits from metadata.setCredits; the shipped defaults are 1.0 / 0.5 / 0.0.

### Swift 6 / iOS

Swift `Codable` can decode only the fields your app needs; unknown DB++ fields are ignored
by default.

```swift
import Foundation

struct Database: Decodable, Sendable {
    let metadata: Metadata
    let exercises: [String: Exercise]
}

struct Metadata: Decodable, Sendable {
    let schemaVersion: String
    let converterVersion: String
    let setCredits: SetCredits
}

struct SetCredits: Decodable, Sendable {
    let direct: Double
    let indirect: Double
    let stabilizer: Double
}

struct Exercise: Decodable, Sendable {
    let exerciseId: String
    let annotation: Annotation
}

struct Annotation: Decodable, Sendable {
    let patterns: [String]
    let direct: [String]
    let indirect: [String]
    let stabilizers: [String]
    let volumeEligible: Bool
    let confidence: String
}
```

## Build from upstream

Requires Python 3.12+. The converter itself uses the standard library; JSON Schema
validation requires `jsonschema`.

```bash
python -m pip install jsonschema

curl -L   https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json   -o exercises.json

python src/convert_fedb_to_fedbpp.py   exercises.json   free-exercise-db-plusplus.json   --schema free-exercise-db-plusplus.schema.json   --completeness full
```

## Repository layout

```text
.
├── README.md
├── LICENSE
├── free-exercise-db-plusplus.json
├── free-exercise-db-plusplus.schema.json
├── workout.schema.json
├── src/
├── tests/
├── docs/
│   └── history/
├── reports/
├── examples/
├── fixtures/
├── mappings/
└── .github/workflows/
```

The main JSON and schemas intentionally remain at the repository root so raw GitHub URLs stay
short and stable for consumers.

## Documentation

- [Methodology](docs/METHODOLOGY.md)
- [Design](docs/DESIGN.md)
- [Evidence policy](docs/EVIDENCE.md)
- [1.0 compatibility contract](docs/COMPATIBILITY.md)
- [Versioning](docs/VERSIONING.md)
- [Release checklist](docs/RELEASE-CHECKLIST.md)
- [Current review report](reports/REVIEW.md)
- [Current rule audit](reports/RULE-AUDIT.md)
- [Current mapping audit](reports/MAPPING-AUDIT.md)
- [Current evidence audit](reports/EVIDENCE-AUDIT.md)

## Version 1.0 contract

Free Exercise DB++ v1.0.0 freezes the public consumer contract described in
[`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md).

The Git release version, `converterVersion`, and `schemaVersion` are intentionally independent:
they identify the project release, generator implementation, and JSON contract revision
respectively. Breaking changes to the 1.0 consumer contract require a new major project release.

## Confidence and evidence

- `high` — deterministic and evidence-backed or explicitly reviewed.
- `medium` — intentional uncertainty from complex-event bookkeeping, indirect evidence, or a
  small number of retained ambiguous mappings.
- `low` — unresolved; release CI is designed to keep used unresolved mappings at zero.

Every used canonical pattern must have non-provisional evidence before CI can pass.
Evidence provenance is embedded in `metadata.evidence` in the main JSON.

## Workout interchange

`workout.schema.json` defines Workout ACTUAL interchange schemas 0.2.0 and 0.3.0: sessions, custom exercises, laterality, structures, macro-segments, and consistent quantity objects. Workout observations reference DB++ exercise definitions using `exerciseId` when available.

Documentation: [Workout interchange guide](docs/WORKOUT-INTERCHANGE.md)

Workout PLAN prescriptions: [PLAN guide](docs/WORKOUT-PLAN.md), [PLAN examples](examples/plans/)

Volume targets and coverage analysis: [TARGET guide](docs/VOLUME-TARGETS.md), [target examples](examples/targets/)

Training context and deterministic plan evaluation: [TrainingProfile](docs/TRAINING-PROFILE.md), [PlanEvaluation](docs/PLAN-EVALUATION.md)

Structured request resolution: [WorkoutIntent](docs/WORKOUT-INTENT.md),
[goal resolution](docs/GOAL-RESOLUTION.md), and
[environment profiles](docs/ENVIRONMENT-PROFILES.md). WorkoutIntent is a
portable structured artifact; natural-language/LLM integration belongs in the
consuming application, not DB++.

Deterministic PLAN proposals: [Plan generation](docs/PLAN-GENERATION.md),
[Planning policies](docs/PLANNING-POLICIES.md).

Derived state and advisory progression: [TrainingState](docs/TRAINING-STATE.md),
[Progression policies](docs/PROGRESSION-POLICIES.md), [CoachDecision](docs/COACH-DECISIONS.md).

PLAN comparison: [PLAN-vs-PLAN guide](docs/PLAN-COMPARISON.md)
PLAN adherence: [PLAN-vs-ACTUAL guide](docs/PLAN-ACTUAL.md)
Normative semantics: [analysis contract](docs/ANALYSIS-SEMANTICS.md)

Longitudinal trainer/research analysis: [longitudinal guide](docs/LONGITUDINAL-ANALYSIS.md)
and [research workflows](docs/RESEARCH-WORKFLOWS.md). For example,
`analyze_periods(TrainingHistory("S001", plans, workouts), db,
period="calendar_week", timezone="America/New_York")` produces deterministic
subject-period-muscle rows without requiring pandas.

Examples: [workout example matrix](examples/workouts/) and [examples/workout.example.json](examples/workout.example.json)

## Exercise families and relationships (v1.5)

The optional `exercise-relationships.json` artifact groups stable exercise IDs
into curated families and records descriptive variation dimensions:

```text
Barbell_Bench_Press_-_Medium_Grip → bench_press → Dumbbell_Bench_Press
```

Family membership is taxonomic/descriptive. It does not mean physiological
equivalence, valid substitution, or automatic replacement of a planned
exercise. Existing explicit PLAN/ACTUAL substitution semantics remain
authoritative. Load it with `fedbpp.RelationshipRegistry`; the artifact has
its own independent schema version and is not required by existing analysis.

## Interoperability (v1.3)

v1.2 provides mapping and capability infrastructure: audited standards documents, structural ACTUAL/category mappings, the reviewed Garmin FIT exercise identity crosswalk, JSON schemas, loss semantics, and deterministic coverage reports. Health Connect session categories are not advertised as exercise identities. Inspect `mappings/`, `docs/interop/`, and `reports/interop/`. Operational import/export serializers remain deferred to v1.3.

Python lookup: `from fedbpp import MappingRegistry; registry = MappingRegistry.load(); registry.lookup_external("garmin-fit", "exercise_name.bench_press.DUMBBELL_BENCH_PRESS")`. Operational FHIR conversion is available with `from fedbpp import import_workout, export_workout`; strict mode is the default. See [import/export](docs/interop/IMPORT-EXPORT.md) and the [CLI](docs/interop/CLI.md). FIT binary, Health Connect, and HealthKit remain explicitly bounded by their API/licensing limitations.

## CI and releases

The build workflow:

1. downloads current upstream Free Exercise DB;
2. checks upstream ID compatibility;
3. builds and validates DB++;
4. verifies reproducibility;
5. runs release-contract, golden-mapping, and medium-confidence policy tests;
6. validates evidence/confidence invariants;
7. generates reports under `reports/`;
8. commits generated public outputs.

The release workflow verifies that the tagged commit matches the reviewed upstream snapshot
before publishing release assets and SHA-256 checksums.

## License

Released under the [Unlicense](LICENSE).


### Analysis semantic contract

PLAN/ACTUAL/TARGET analysis uses the named `dbpp-default-volume-v1` counting policy and authoritative `metadata.setCredits`. It preserves prescription ranges—including unspecified bounds—excludes `volumeEligible=false` exercises from resistance-volume totals while reporting them in completeness diagnostics, separates unplanned ACTUAL work, and records reproducibility provenance. See the [normative analysis semantics](docs/ANALYSIS-SEMANTICS.md).


## Adaptive coaching (v1.9)

The packaged Python API exposes deterministic advisory coaching: `from fedbpp.coaching import adapt_plan, COACHING_POLICIES`. It derives or accepts canonical TrainingState, emits explainable CoachDecision records, and returns an immutable proposed PLAN only after canonical validation and evaluation. DB++ never assigns, activates, sends, persists, or accepts a proposal. See [Adaptive coaching](docs/ADAPTIVE-COACHING.md).
