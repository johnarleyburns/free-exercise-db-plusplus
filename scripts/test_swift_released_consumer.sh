#!/usr/bin/env bash
set -euo pipefail

# Post-release smoke: resolve the package by its published semantic version,
# with the temporary consumer and its working directory outside this repository.
version=${SWIFT_RELEASE_VERSION:-1.12.0}
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/Sources/Consumer"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Consumer", dependencies: [.package(url: "https://github.com/johnarleyburns/free-exercise-db-plusplus.git", exact: "$version")], targets: [.executableTarget(name: "Consumer", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "free-exercise-db-plusplus")])])
EOF
cat > "$consumer/Sources/Consumer/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus

let engine = try TrainingEngine.bundled()
let intent = WorkoutIntent(
  goal: "hypertrophy", environment: "commercial_gym",
  schedule: WorkoutSchedule(cycleLengthDays: 7, sessionsPerCycle: IntRange(target: 3)))
precondition(engine.validateIntent(intent).isValid)
let resolution = engine.resolveIntent(intent)
guard let profile = resolution.resolvedTrainingProfile,
      let target = resolution.resolvedVolumeTarget else {
  throw FEDBError.invalidDocument("released smoke resolution did not produce typed context")
}
let generated = engine.generatePlan(request: PlanGenerationRequest(profile: profile, target: target))
guard let plan = generated.plan else { throw FEDBError.invalidDocument("released smoke did not generate a plan") }
let planRoundTrip = try JSONDecoder().decode(WorkoutPlan.self, from: JSONEncoder().encode(plan))
precondition(planRoundTrip == plan)
let evaluation = engine.evaluatePlan(plan, profile: profile, target: target)
let history = TrainingHistory(subjectId: "released-smoke", plans: [plan])
let asOf = Date(timeIntervalSince1970: 1_790_812_800)
let state = try engine.deriveTrainingState(history: history, asOf: asOf)
let adapted = engine.adaptPlan(request: PlanAdaptationRequest(
  profile: profile, target: target, currentPlan: plan, history: history, asOf: asOf))
let resultRoundTrip = try JSONDecoder().decode(AdaptivePlanResult.self, from: JSONEncoder().encode(adapted))
precondition(resultRoundTrip == adapted)
print("released Swift consumer ok: generation=\(generated.status), evaluation=\(evaluation.status), state=\(state.subjectId), adaptation=\(adapted.status)")
EOF
(cd /tmp && swift run --package-path "$consumer" Consumer)
