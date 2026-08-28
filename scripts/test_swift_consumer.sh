#!/usr/bin/env bash
set -euo pipefail

# Build an external executable in a temporary directory.  The consumer never
# relies on the package's checkout as its current directory.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
jq -S '{environmentPolicies,goalPolicies}' "$repo/resources/intent-policies.json" | cmp - <(jq -S '{environmentPolicies,goalPolicies}' "$repo/packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources/intent-policies.json")
mkdir -p "$consumer/Sources/Consumer"
cp "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json" "$consumer/intent.json"
cp "$repo/fixtures/cross-language/history/input.json" "$consumer/history.json"
cp "$repo/fixtures/cross-language/adaptation/input.json" "$consumer/adaptation.json"
cp "$repo/fixtures/cross-language/evaluation/input.json" "$consumer/evaluation.json"
cp "$repo/fixtures/cross-language/generation/input.json" "$consumer/generation.json"
mkdir -p "$consumer/out"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Consumer", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Consumer", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF
cat > "$consumer/Sources/Consumer/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus
let intent = try JSONDecoder().decode(WorkoutIntent.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
let engine = try TrainingEngine.bundled()
let intentEngine = TrainingEngine(database: engine.database)
let result = engine.resolveIntent(intent)
precondition(result.status == "resolved_with_defaults")
precondition(result.goalPolicy?.policyId == "general-hypertrophy-v1")
precondition(result.defaultsApplied == ["goalPolicy", "planningPolicy", "environmentPolicy"])
precondition(result.explicitOverrides == ExplicitOverrides())
let profile = result.resolvedProfile!
let target = result.resolvedTarget!
let generatedFromIntent = intentEngine.generatePlanFromIntent(intent)
precondition(generatedFromIntent.objectValue?["resolution"] != nil)
let generated = generatedFromIntent.objectValue?["generation"] ?? engine.generatePlan(profile: profile, target: target, policy: result.planningPolicy ?? "full-body-general-v1")
precondition(generated.objectValue?["plan"] != .null)
let evaluated = intentEngine.evaluatePlan(generated.objectValue?["plan"] ?? .null, profile: profile, target: target)
precondition(generated.objectValue?["evaluation"] == evaluated)
let encoder = JSONEncoder()
func load(_ path: String) throws -> JSONValue { try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: URL(fileURLWithPath: path))) }
func write(_ name: String, _ value: JSONValue) throws { try encoder.encode(value).write(to: URL(fileURLWithPath: CommandLine.arguments[6]).appendingPathComponent(name)) }
let evaluationInput = try load(CommandLine.arguments[4])
try write("evaluation.json", engine.evaluatePlan(evaluationInput.objectValue?["plan"] ?? .null, profile: evaluationInput.objectValue?["profile"], target: evaluationInput.objectValue?["target"]))
let generationInput = try load(CommandLine.arguments[5])
try write("generation.json", engine.generatePlan(profile: generationInput.objectValue?["profile"] ?? .null, target: generationInput.objectValue?["target"] ?? .null, policy: "full-body-general-v1", requiredExerciseIds: ["Barbell_Bench_Press_-_Medium_Grip"]))
try write("intent-resolution.json", try JSONDecoder().decode(JSONValue.self, from: encoder.encode(intentEngine.resolveIntent(intent))))
try write("intent-generation.json", intentEngine.generatePlanFromIntent(intent))
let history = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2])))
let state = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00-04:00")
precondition(state.objectValue?["stateVersion"] != nil)
let adaptation = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[3])))
let adaptationAsOf: String? = if case .string(let value)? = adaptation.objectValue?["asOf"] { value } else { nil }
let adapted = engine.adaptPlan(profile: adaptation.objectValue?["profile"] ?? profile, target: adaptation.objectValue?["target"] ?? target, currentPlan: adaptation.objectValue?["currentPlan"] ?? .null, history: adaptation.objectValue?["history"], asOf: adaptationAsOf)
precondition(adapted.objectValue?["currentPlan"] != nil)
try write("history.json", state)
try write("adaptation.json", adapted)
print("swift consumer ok")
EOF
swift run --package-path "$consumer" Consumer "$consumer/intent.json" "$consumer/history.json" "$consumer/adaptation.json" "$consumer/evaluation.json" "$consumer/generation.json" "$consumer/out"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/evaluation/expected.json" "$consumer/out/evaluation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/history/expected.json" "$consumer/out/history.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/generation/expected.json" "$consumer/out/generation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/adaptation/expected.json" "$consumer/out/adaptation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-resolution.json" "$consumer/out/intent-resolution.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-generation.json" "$consumer/out/intent-generation.json"
echo "swift consumer goldens ok"
