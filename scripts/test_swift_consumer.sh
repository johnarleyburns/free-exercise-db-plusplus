#!/usr/bin/env bash
set -euo pipefail

# Build an external executable in a temporary directory.  The consumer never
# relies on the package's checkout as its current directory.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/Sources/Consumer"
cp "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json" "$consumer/intent.json"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Consumer", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Consumer", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF
cat > "$consumer/Sources/Consumer/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus
let intent = try JSONDecoder().decode(WorkoutIntent.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
let result = resolveIntent(intent)
precondition(result.status == "resolved_with_defaults")
precondition(result.goalPolicy?.policyId == "general-hypertrophy-v1")
precondition(result.defaultsApplied == ["goalPolicy", "planningPolicy", "environmentPolicy"])
precondition(result.explicitOverrides == ExplicitOverrides())
print("swift consumer ok")
EOF
swift run --package-path "$consumer" Consumer "$consumer/intent.json"
