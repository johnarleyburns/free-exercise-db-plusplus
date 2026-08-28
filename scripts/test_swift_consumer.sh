#!/usr/bin/env bash
set -euo pipefail

# This consumer is deliberately created outside the repository and works when
# invoked from any current directory. It exercises only the typed app surface.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/Sources/Consumer"

cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Consumer", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Consumer", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF

cat > "$consumer/Sources/Consumer/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus

let root = URL(fileURLWithPath: CommandLine.arguments[1])
let decoder = JSONDecoder()
let encoder = JSONEncoder()
let engine = try TrainingEngine.bundled()

func read<T: Decodable>(_ type: T.Type, _ path: String) throws -> T {
  try decoder.decode(type, from: Data(contentsOf: root.appendingPathComponent(path)))
}
func date(_ value: String) throws -> Date {
  let formatter = ISO8601DateFormatter()
  formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
  if let result = formatter.date(from: value) { return result }
  formatter.formatOptions = [.withInternetDateTime]
  guard let result = formatter.date(from: value) else { throw FEDBError.invalidDocument("invalid test timestamp") }
  return result
}
func require<T>(_ value: T?, _ message: String) throws -> T {
  guard let value else { throw FEDBError.invalidDocument(message) }
  return value
}

let intent: WorkoutIntent = try read(WorkoutIntent.self, "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")
let validation = engine.validateIntent(intent)
precondition(validation.isValid)
let resolution = engine.resolveIntent(intent)
precondition(["resolved", "resolved_with_defaults"].contains(resolution.status))
let profile = try decoder.decode(TrainingProfile.self, from: encoder.encode(try require(resolution.resolvedProfile, "missing profile")))
let target = try decoder.decode(VolumeTarget.self, from: encoder.encode(try require(resolution.resolvedTarget, "missing target")))

let generated = engine.generatePlan(request: PlanGenerationRequest(profile: profile, target: target, policy: resolution.planningPolicy ?? "full-body-general-v1"))
precondition(generated.status == "generated")
let plan = try require(generated.plan, "missing generated plan")
let evaluated = engine.evaluatePlan(plan, profile: profile, target: target)
precondition(evaluated.status == generated.evaluation?.status)
let planRoundTrip = try decoder.decode(WorkoutPlan.self, from: encoder.encode(plan))
let generatedRoundTrip = try decoder.decode(GeneratedPlanResult.self, from: encoder.encode(generated))
let evaluationRoundTrip = try decoder.decode(PlanEvaluation.self, from: encoder.encode(evaluated))
precondition(planRoundTrip == plan)
precondition(generatedRoundTrip == generated)
precondition(evaluationRoundTrip == evaluated)

let history: TrainingHistory = try read(TrainingHistory.self, "fixtures/cross-language/history/input.json")
let state = try engine.deriveTrainingState(history: history, asOf: date("2026-08-27T12:00:00-04:00"))
precondition(state.subjectId == history.subjectId)
let stateRoundTrip = try decoder.decode(TrainingState.self, from: encoder.encode(state))
precondition(stateRoundTrip == state)

let adaptationInput: JSONValue = try read(JSONValue.self, "fixtures/cross-language/adaptation/input.json")
let adaptationObject = try require(adaptationInput.objectValue, "invalid adaptation input")
let adaptationProfile = try decoder.decode(TrainingProfile.self, from: encoder.encode(try require(adaptationObject["profile"], "missing adaptation profile")))
let adaptationTarget = try decoder.decode(VolumeTarget.self, from: encoder.encode(try require(adaptationObject["target"], "missing adaptation target")))
let adaptationPlan = try decoder.decode(WorkoutPlan.self, from: encoder.encode(try require(adaptationObject["currentPlan"], "missing adaptation plan")))
let adaptationHistory = try decoder.decode(TrainingHistory.self, from: encoder.encode(try require(adaptationObject["history"], "missing adaptation history")))
let adapted = engine.adaptPlan(request: PlanAdaptationRequest(profile: adaptationProfile, target: adaptationTarget, currentPlan: adaptationPlan, history: adaptationHistory, asOf: try date("2026-08-27T12:00:00Z")))
precondition(adapted.currentPlan == adaptationPlan)
let adaptationRoundTrip = try decoder.decode(AdaptivePlanResult.self, from: encoder.encode(adapted))
precondition(adaptationRoundTrip == adapted)

print("typed external Swift consumer ok: plan=\(plan.planId)/\(plan.revisionId), state=\(state.exerciseState.count), adaptation=\(adapted.status)")
EOF

(cd /tmp && swift run --package-path "$consumer" Consumer "$repo")
echo "swift external consumer ok"
