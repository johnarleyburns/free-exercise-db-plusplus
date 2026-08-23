# Free Exercise DB++

Free Exercise DB++ is a reproducible, evidence-audited annotation layer over
[yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db).

It preserves every upstream exercise record and adds normalized classification plus resistance-training volume annotations suitable for apps, training logs, and research-oriented analysis.

## Runtime artifact

Consumers need only one data file:

```text
free-exercise-db-plusplus.json
```

The JSON Schema is optional validation tooling.

Each exercise adds:

- `classification.trainingTypes`
- `classification.modalities`
- `classification.sportContexts`
- `classification.competitionMovements`
- `annotation.patterns`
- `annotation.direct`
- `annotation.indirect`
- `annotation.stabilizers`
- `annotation.volumeEligible`
- `annotation.confidence`
- `annotation.reviewReasons`
- `annotation.evidenceRefs`

The complete original Free Exercise DB record remains under `source`.

## Set accounting

DB++ uses one set-credit model:

```json
{
  "direct": 1.0,
  "indirect": 0.5,
  "stabilizer": 0.0
}
```

See `METHODOLOGY.md` for definitions and interpretation.

## Generate DB++

```bash
python3 convert_fedb_to_fedbpp.py   exercises.json   free-exercise-db-plusplus.json   --schema free-exercise-db-plusplus.schema.json   --completeness full
```

The converter itself uses the Python standard library. Schema validation requires:

```bash
python3 -m pip install jsonschema
```

Upstream combined JSON:

```text
https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json
```

## Python ingestion

```python
import json

with open("free-exercise-db-plusplus.json", encoding="utf-8") as f:
    db = json.load(f)

bench = db["exercises"]["Barbell_Bench_Press_-_Medium_Grip"]

print(bench["annotation"]["direct"])
print(bench["annotation"]["indirect"])
print(db["metadata"]["setCredits"])
```

Example effective-set calculation:

```python
from collections import defaultdict

performed_sets = {
    "Barbell_Bench_Press_-_Medium_Grip": 4,
}

credits = db["metadata"]["setCredits"]
effective = defaultdict(float)

for exercise_id, sets in performed_sets.items():
    ann = db["exercises"][exercise_id]["annotation"]

    if not ann["volumeEligible"]:
        continue

    for muscle in ann["direct"]:
        effective[muscle] += sets * credits["direct"]

    for muscle in ann["indirect"]:
        effective[muscle] += sets * credits["indirect"]

print(dict(effective))
```

## Swift 6 / iOS ingestion

A minimal model can decode only the fields your app needs; Swift `Codable` ignores unknown JSON keys by default.

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
    let classification: Classification
    let annotation: Annotation
}

struct Classification: Decodable, Sendable {
    let trainingTypes: [String]
    let modalities: [String]
    let sportContexts: [String]
    let competitionMovements: [String]
}

struct Annotation: Decodable, Sendable {
    let patterns: [String]
    let direct: [String]
    let indirect: [String]
    let stabilizers: [String]
    let volumeEligible: Bool
    let confidence: String
    let reviewReasons: [String]
    let evidenceRefs: [String]
}
```

Load a bundled asset:

```swift
let url = Bundle.main.url(
    forResource: "free-exercise-db-plusplus",
    withExtension: "json"
)!
let data = try Data(contentsOf: url)
let database = try JSONDecoder().decode(Database.self, from: data)
```

## Evidence and confidence

Evidence provenance is embedded directly into the generated JSON under:

```text
metadata.evidence.references
metadata.evidence.patterns
```

Used patterns must not remain `provisional`.

Confidence values:

- `high` — deterministic/evidence-backed or explicitly reviewed mapping
- `medium` — complex-event bookkeeping, indirect evidence, or retained ambiguity
- `low` — unresolved; release CI is intended to keep this at zero

See `METHODOLOGY.md`.

## CI and reproducibility

GitHub Actions:

1. downloads current upstream Free Exercise DB;
2. builds DB++;
3. validates it against JSON Schema;
4. verifies evidence references and confidence rules;
5. runs release-contract invariants;
6. builds twice with a fixed `SOURCE_DATE_EPOCH` and requires byte-identical output;
7. generates review/evidence/rule/mapping/fallback audits;
8. commits generated public outputs on non-PR builds.

The generated metadata includes the upstream SHA-256 for traceability.

## Workout interchange

`workout.schema.json` defines a separate set-level workout/session interchange format that references exercises by stable `exerciseId`.

Exercise definitions and workout observations intentionally remain separate.

## Versioning

See `VERSIONING.md`.

Current data schema: **0.3.0**  
Current converter: **0.8.0**
