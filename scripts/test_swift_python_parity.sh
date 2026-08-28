#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
out=$(mktemp -d)
trap 'rm -rf "$consumer" "$out"' EXIT
mkdir -p "$consumer/Sources/Parity"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Parity", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Parity", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF
cat > "$consumer/Sources/Parity/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus

let root = URL(fileURLWithPath: CommandLine.arguments[1])
let out = URL(fileURLWithPath: CommandLine.arguments[2])
let decoder = JSONDecoder(); let encoder = JSONEncoder()
let db = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
let load: (String) throws -> JSONValue = { try decoder.decode(JSONValue.self, from: Data(contentsOf: root.appendingPathComponent($0))) }
let relationships = try decoder.decode(ExerciseRelationships.self, from: encoder.encode(load("fixtures/cross-language/evaluation/input.json").objectValue!["relationships"]!))
let engine = TrainingEngine(database: db, relationships: relationships)
let intentEngine = TrainingEngine(database: db)
func write(_ name: String, _ value: JSONValue) throws { try encoder.encode(value).write(to: out.appendingPathComponent(name)) }

let evaluation = try load("fixtures/cross-language/evaluation/input.json")
try write("evaluation.json", engine.evaluatePlan(evaluation.objectValue!["plan"]!, profile: evaluation.objectValue!["profile"]!, target: evaluation.objectValue!["target"]!))
let history = try load("fixtures/cross-language/history/input.json")
try write("history.json", engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00-04:00"))
let generation = try load("fixtures/cross-language/generation/input.json")
try write("generation.json", engine.generatePlan(profile: generation.objectValue!["profile"]!, target: generation.objectValue!["target"]!, policy: "full-body-general-v1", requiredExerciseIds: ["Barbell_Bench_Press_-_Medium_Grip"]))
let adaptation = try load("fixtures/cross-language/adaptation/input.json")
try write("adaptation.json", engine.adaptPlan(profile: adaptation.objectValue!["profile"]!, target: adaptation.objectValue!["target"]!, currentPlan: adaptation.objectValue!["currentPlan"]!, history: adaptation.objectValue!["history"], asOf: "2026-08-27T12:00:00Z"))
let progressionRaw = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/progression/input.json"))) as! [String: Any]
let progressionPolicy = progressionRaw["policy"] as! String
let progressionParameters = try decoder.decode(JSONValue.self, from: JSONSerialization.data(withJSONObject: progressionRaw["parameters"]!))
var progressionResults: [String: JSONValue] = [:]
for item in progressionRaw["cases"] as! [[String: Any]] {
  let prescription = try decoder.decode(JSONValue.self, from: JSONSerialization.data(withJSONObject: item["prescription"]!))
  let state = try decoder.decode(JSONValue.self, from: JSONSerialization.data(withJSONObject: item["state"]!))
  progressionResults[item["id"] as! String] = engine.applyProgressionPolicy(progressionPolicy, prescription: prescription, exerciseState: state, parameters: progressionParameters)
}
try write("progression.json", .object(progressionResults))
let intentDir = root.appendingPathComponent("fixtures/cross-language/intent/flagship-5day-hypertrophy")
let intent = try decoder.decode(WorkoutIntent.self, from: Data(contentsOf: intentDir.appendingPathComponent("input.json")))
let resolution = intentEngine.resolveIntent(intent)
try encoder.encode(resolution).write(to: out.appendingPathComponent("intent-resolution.json"))
try encoder.encode(FreeExerciseDBPlusPlus.generatePlanFromIntent(intent, database: db)).write(to: out.appendingPathComponent("intent-generation.json"))
let intentRoot = root.appendingPathComponent("fixtures/cross-language/intent")
for directory in try FileManager.default.contentsOfDirectory(at: intentRoot, includingPropertiesForKeys: [.isDirectoryKey]) where (try directory.resourceValues(forKeys: [.isDirectoryKey]).isDirectory == true) {
  let name = directory.lastPathComponent
  guard let input = try? decoder.decode(WorkoutIntent.self, from: Data(contentsOf: directory.appendingPathComponent("input.json"))) else { continue }
  let history = name == "history-aware" ? try load("fixtures/cross-language/intent/history-aware/history.json") : nil
  let explicitTarget = name == "target-partial-override" ? try load("fixtures/cross-language/intent/target-partial-override/target.json") : nil
  let resolved = FreeExerciseDBPlusPlus.resolveIntent(input, database: db, target: explicitTarget, history: history, asOf: name == "history-aware" ? "2026-08-25T12:00:00Z" : nil)
  try encoder.encode(resolved).write(to: out.appendingPathComponent("intent-resolution-\(name).json"))
}
EOF
swift run --package-path "$consumer" Parity "$repo" "$out" >/dev/null
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/evaluation/expected.json" "$out/evaluation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/history/expected.json" "$out/history.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/generation/expected.json" "$out/generation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/adaptation/expected.json" "$out/adaptation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/progression/expected.json" "$out/progression.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-resolution.json" "$out/intent-resolution.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-generation.json" "$out/intent-generation.json"
for fixture in "$repo"/fixtures/cross-language/intent/*/expected-resolution.json; do
  name=$(basename "$(dirname "$fixture")")
  echo "checking intent $name"
  python3 "$repo/tools/compare_canonical_json.py" "$fixture" "$out/intent-resolution-$name.json"
done
echo "Swift/Python parity goldens ok"
