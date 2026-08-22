# Free Exercise DB++

Free Exercise DB++ is a reproducible annotation layer over [yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db).

It preserves each upstream exercise record and adds a training-volume model intended for strength/hypertrophy tracking:

- `direct` muscle: default 1.0 set credit
- `indirect` muscle: default 0.5 set credit
- `stabilizer` muscle: default 0.0 set credit
- `volumeEligible`: whether the exercise should contribute to resistance-training set totals
- `patterns`: canonical movement-pattern labels
- `confidence`: `high`, `medium`, or `low`
- `reviewReasons`: why a mapping should be independently checked

## Files

- `DESIGN.md` — human-readable design and biomechanics/annotation principles.
- `convert_fedb_to_fedbpp.py` — deterministic Python converter.
- `free-exercise-db-plusplus.schema.json` — JSON Schema Draft 2020-12 contract.
- `free-exercise-db-plusplus.json` — generated verification artifact included with this package.
- `upstream-verification-fixture.json` — small source fixture used for the included generated artifact.

> Important: the included `free-exercise-db-plusplus.json` is a **verification fixture**, not the complete 800+ exercise database, because the build runtime used for this first package could not materialize the full upstream JSON. Its metadata explicitly says `completeness: "fixture"`. Running the converter against the upstream combined JSON produces the full database.

Free Exercise DB itself publishes a combined JSON at:

`https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json`

The upstream project documents 800+ exercises and provides its own JSON Schema. Free Exercise DB is distributed under the Unlicense.

## Generate the full DB++

Download the upstream combined file, then run:

```bash
python3 convert_fedb_to_fedbpp.py \
  exercises.json \
  free-exercise-db-plusplus.json \
  --schema free-exercise-db-plusplus.schema.json \
  --completeness full
```

Optional dependency for schema validation:

```bash
python3 -m pip install jsonschema
```

The converter itself uses only the Python standard library. `jsonschema` is required only when `--schema` is passed.

## GitHub Actions build

`.github/workflows/build-db.yml` reproducibly builds the full DB++ on an Ubuntu GitHub runner. It downloads the current upstream combined JSON, runs the converter with `--completeness full`, validates the result against the Draft 2020-12 schema, performs basic count/completeness assertions, and uploads `free-exercise-db-plusplus.json` as a workflow artifact.

The workflow runs on relevant pushes and pull requests, can be triggered manually, and also runs weekly so upstream compatibility problems are surfaced even when this repository has not changed. It intentionally does **not** auto-commit regenerated data; upstream changes should be reviewed before becoming a repository commit.

## Python ingestion

### Load the dataset

```python
import json
from pathlib import Path

path = Path("free-exercise-db-plusplus.json")

with path.open("r", encoding="utf-8") as f:
    db = json.load(f)

print(db["metadata"]["schemaVersion"])
print(len(db["exercises"]))

bench = db["exercises"]["Barbell_Bench_Press_-_Medium_Grip"]
print(bench["annotation"]["direct"])
print(bench["annotation"]["indirect"])
```

### Validate against JSON Schema

```python
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

with Path("free-exercise-db-plusplus.schema.json").open() as f:
    schema = json.load(f)

with Path("free-exercise-db-plusplus.json").open() as f:
    db = json.load(f)

validator = Draft202012Validator(
    schema,
    format_checker=FormatChecker()
)

errors = sorted(
    validator.iter_errors(db),
    key=lambda e: list(e.absolute_path)
)

if errors:
    for error in errors:
        print(f"{list(error.absolute_path)}: {error.message}")
    raise SystemExit(1)

print("DB++ schema validation passed")
```

### Calculate effective weekly sets

```python
from collections import defaultdict

credits = db["metadata"]["setCredits"]

# Example log: exercise ID -> performed sets
training = {
    "Barbell_Bench_Press_-_Medium_Grip": 4,
    "Alternate_Incline_Dumbbell_Curl": 3,
}

effective_sets = defaultdict(float)

for exercise_id, performed_sets in training.items():
    ann = db["exercises"][exercise_id]["annotation"]

    if not ann["volumeEligible"]:
        continue

    for muscle in ann["direct"]:
        effective_sets[muscle] += performed_sets * credits["direct"]

    for muscle in ann["indirect"]:
        effective_sets[muscle] += performed_sets * credits["indirect"]

    # Stabilizers intentionally add zero by default.

print(dict(effective_sets))
```

## Swift 6 / iOS ingestion

For iOS apps, the simplest robust architecture is:

1. validate the DB++ asset against the JSON Schema in CI/build tooling;
2. bundle the validated JSON with the app, or download a versioned validated asset;
3. decode it at runtime with Swift 6 `Codable`.

That avoids requiring a JSON-Schema engine in the shipping iOS app.

### Swift 6 Codable models

```swift
import Foundation

struct FEDBPlusPlus: Codable, Sendable {
    let metadata: Metadata
    let exercises: [String: ExerciseRecord]
}

struct Metadata: Codable, Sendable {
    let schemaVersion: String
    let converterVersion: String
    let generatedAt: String
    let upstream: Upstream
    let setCredits: SetCredits
    let muscleOntology: [String]
    let sourceExerciseCount: Int
    let outputExerciseCount: Int
    let completeness: String
}

struct Upstream: Codable, Sendable {
    let project: String
    let sourceUrl: String
    let sha256: String?
}

struct SetCredits: Codable, Sendable {
    let direct: Double
    let indirect: Double
    let stabilizer: Double
}

struct ExerciseRecord: Codable, Sendable {
    let exerciseId: String
    let annotation: Annotation
    let source: SourceExercise
}

struct Annotation: Codable, Sendable {
    let patterns: [String]
    let direct: [String]
    let indirect: [String]
    let stabilizers: [String]
    let volumeEligible: Bool
    let confidence: Confidence
    let reviewReasons: [String]
}

enum Confidence: String, Codable, Sendable {
    case high
    case medium
    case low
}

struct SourceExercise: Codable, Sendable {
    let id: String
    let name: String
    let force: String?
    let level: String
    let mechanic: String?
    let equipment: String?
    let primaryMuscles: [String]
    let secondaryMuscles: [String]
    let instructions: [String]
    let category: String
    let images: [String]
}
```

If the upstream schema later adds fields, strict `SourceExercise` decoding may need updating. If you want maximum forward compatibility, keep only the source fields your app actually uses, or decode `source` into a general JSON value type.

### Load a bundled DB++ file

Add `free-exercise-db-plusplus.json` to the app target and:

```swift
import Foundation

enum ExerciseDatabaseError: Error {
    case missingResource
}

func loadExerciseDatabase() throws -> FEDBPlusPlus {
    guard let url = Bundle.main.url(
        forResource: "free-exercise-db-plusplus",
        withExtension: "json"
    ) else {
        throw ExerciseDatabaseError.missingResource
    }

    let data = try Data(contentsOf: url)
    return try JSONDecoder().decode(FEDBPlusPlus.self, from: data)
}
```

### Load asynchronously from a URL

```swift
import Foundation

func fetchExerciseDatabase(from url: URL) async throws -> FEDBPlusPlus {
    let (data, response) = try await URLSession.shared.data(from: url)

    if let http = response as? HTTPURLResponse {
        guard (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }

    return try JSONDecoder().decode(FEDBPlusPlus.self, from: data)
}
```

### Calculate effective sets in Swift 6

```swift
import Foundation

struct SetContribution: Sendable {
    var direct: Double = 0
    var indirect: Double = 0

    var effective: Double {
        direct + indirect
    }
}

func effectiveVolume(
    database: FEDBPlusPlus,
    performedSets: [String: Int]
) -> [String: SetContribution] {
    var result: [String: SetContribution] = [:]

    for (exerciseID, setCount) in performedSets {
        guard
            let exercise = database.exercises[exerciseID],
            exercise.annotation.volumeEligible
        else {
            continue
        }

        for muscle in exercise.annotation.direct {
            var contribution = result[muscle, default: .init()]
            contribution.direct +=
                Double(setCount) * database.metadata.setCredits.direct
            result[muscle] = contribution
        }

        for muscle in exercise.annotation.indirect {
            var contribution = result[muscle, default: .init()]
            contribution.indirect +=
                Double(setCount) * database.metadata.setCredits.indirect
            result[muscle] = contribution
        }
    }

    return result
}
```

## JSON Schema and Swift

JSON Schema is intentionally included as the **normative structural contract**, even though `Codable` is the preferred runtime ingestion mechanism on iOS.

Recommended workflow:

```text
upstream FEDB
      │
      ▼
Python converter
      │
      ▼
DB++ JSON ──► JSON Schema validation in CI
      │
      ▼
versioned/bundled asset
      │
      ▼
Swift 6 Codable
```

This provides two independent checks:

- JSON Schema validates the producer/output format.
- Swift `Codable` validates the subset the app expects to consume.

If a project specifically requires runtime JSON-Schema validation on Apple platforms, use a maintained Swift package that supports the required JSON Schema draft and pin its version. We intentionally do not make FEDB++ depend on a specific third-party Swift validator.

## Schema-version compatibility

Consumers should inspect:

```json
"schemaVersion": "0.1.0"
```

before ingestion. During pre-1.0 development, assume minor releases can add fields or muscle patterns. Consumers should therefore ignore unknown JSON properties where practical.

## Auditability

Every DB++ record retains the entire original exercise under:

```json
"source": { ... }
```

This is deliberate. A reviewer can compare upstream metadata against:

```json
"annotation": {
  "patterns": [],
  "direct": [],
  "indirect": [],
  "stabilizers": [],
  "volumeEligible": true,
  "confidence": "high",
  "reviewReasons": []
}
```

The mapping is generated by explicit converter rules, and ambiguous fallback classifications are flagged rather than silently treated as authoritative.

## v0.2 audit build

The GitHub Actions build now generates the full DB++ from the current upstream dataset and publishes a build artifact containing the generated JSON plus `REVIEW.md`, `review-queue.csv`, and `review-summary.json`.

The review queue is intentional: rule-based compound mappings remain medium confidence, while unrecognized compound movements are low confidence. Development should prioritize the low-confidence queue and convert recurring families into reviewed rules/overrides.
