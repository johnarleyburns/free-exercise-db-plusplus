#!/usr/bin/env bash
set -euo pipefail

# Build an external executable in a temporary directory.  The consumer never
# relies on the package's checkout as its current directory.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/Sources/Consumer"
cp "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json" "$consumer/intent.json"
cp "$repo/fixtures/cross-language/history/input.json" "$consumer/history.json"
cp "$repo/fixtures/cross-language/adaptation/input.json" "$consumer/adaptation.json"
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
let result = engine.resolveIntent(intent)
precondition(result.status == "resolved_with_defaults")
precondition(result.goalPolicy?.policyId == "general-hypertrophy-v1")
precondition(result.defaultsApplied == ["goalPolicy", "planningPolicy", "environmentPolicy"])
precondition(result.explicitOverrides == ExplicitOverrides())
let profile = result.resolvedProfile!
let target = result.resolvedTarget!
let generated = engine.generatePlan(profile: profile, target: target, policy: result.planningPolicy ?? "full-body-general-v1")
precondition(generated.objectValue?["plan"] != .null)
let evaluated = engine.evaluatePlan(generated.objectValue?["plan"] ?? .null, profile: profile, target: target)
precondition(generated.objectValue?["evaluation"] == evaluated)
let history = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2])))
let state = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00-04:00")
precondition(state.objectValue?["stateVersion"] != nil)
let adaptation = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[3])))
let adaptationAsOf: String? = if case .string(let value)? = adaptation.objectValue?["asOf"] { value } else { nil }
let adapted = engine.adaptPlan(profile: adaptation.objectValue?["profile"] ?? profile, target: adaptation.objectValue?["target"] ?? target, currentPlan: adaptation.objectValue?["currentPlan"] ?? .null, history: adaptation.objectValue?["history"], asOf: adaptationAsOf)
precondition(adapted.objectValue?["currentPlan"] != nil)
print("swift consumer ok")
EOF
swift run --package-path "$consumer" Consumer "$consumer/intent.json" "$consumer/history.json" "$consumer/adaptation.json"
