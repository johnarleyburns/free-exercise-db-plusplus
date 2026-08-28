#!/usr/bin/env bash
set -euo pipefail

# Informational smoke only: no wall-clock threshold is used in CI.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/Sources/Benchmark"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Benchmark", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Benchmark", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF
cat > "$consumer/Sources/Benchmark/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus

let clock = ContinuousClock()
let initStart = clock.now
let engine = try TrainingEngine.bundled()
let initTime = initStart.duration(to: clock.now)
let root = URL(fileURLWithPath: CommandLine.arguments[1])
let decoder = JSONDecoder()
let intent = try decoder.decode(WorkoutIntent.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")))
let resolutionStart = clock.now
let resolution = engine.resolveIntent(intent)
let resolutionTime = resolutionStart.duration(to: clock.now)
func require<T>(_ value: T?, _ message: String) throws -> T {
  guard let value else { throw NSError(domain: "Benchmark", code: 1, userInfo: [NSLocalizedDescriptionKey: message]) }
  return value
}
let profile = try decoder.decode(TrainingProfile.self, from: JSONEncoder().encode(try require(resolution.resolvedProfile, "missing profile")))
let target = try decoder.decode(VolumeTarget.self, from: JSONEncoder().encode(try require(resolution.resolvedTarget, "missing target")))
let generationStart = clock.now
let generated = engine.generatePlan(request: PlanGenerationRequest(profile: profile, target: target))
let generationTime = generationStart.duration(to: clock.now)
let history = try decoder.decode(TrainingHistory.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/history/input.json")))
let stateStart = clock.now
let asOf = try require(ISO8601DateFormatter().date(from: "2026-08-27T12:00:00Z"), "invalid as-of date")
let state = try engine.deriveTrainingState(history: history, asOf: asOf)
let stateTime = stateStart.duration(to: clock.now)
precondition(generated.plan != nil && state.subjectId == history.subjectId)
print("Swift smoke timings: init=\(initTime), resolve=\(resolutionTime), generate=\(generationTime), state=\(stateTime)")
EOF
(cd /tmp && swift run --package-path "$consumer" Benchmark "$repo")
