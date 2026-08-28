#!/usr/bin/env bash
set -euo pipefail

# External consumer parity for the transport-neutral application contract.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
out=$(mktemp -d)
trap 'rm -rf "$consumer" "$out"' EXIT
mkdir -p "$consumer/Sources/Consumer"
cat > "$consumer/Package.swift" <<EOF
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "ApplicationConsumer", dependencies: [.package(path: "$repo/packages/swift/FreeExerciseDBPlusPlus")], targets: [.executableTarget(name: "Consumer", dependencies: [.product(name: "FreeExerciseDBPlusPlus", package: "FreeExerciseDBPlusPlus")])])
EOF
cat > "$consumer/Sources/Consumer/main.swift" <<'EOF'
import Foundation
import FreeExerciseDBPlusPlus

let root = URL(fileURLWithPath: CommandLine.arguments[1])
let out = URL(fileURLWithPath: CommandLine.arguments[2])
let decoder = JSONDecoder()
let encoder = JSONEncoder()
let engine = try TrainingEngine.bundled()
let names = try FileManager.default.contentsOfDirectory(atPath: root.path).sorted()
for name in names {
  let directory = root.appendingPathComponent(name)
  var isDirectory: ObjCBool = false
  guard FileManager.default.fileExists(atPath: directory.path, isDirectory: &isDirectory), isDirectory.boolValue else { continue }
  let request = try decoder.decode(TrainingRequest.self, from: Data(contentsOf: directory.appendingPathComponent("request.json")))
  let result = try engine.processTrainingRequest(request)
  let resultDirectory = out.appendingPathComponent(name)
  try FileManager.default.createDirectory(at: resultDirectory, withIntermediateDirectories: true)
  try encoder.encode(result).write(to: resultDirectory.appendingPathComponent("actual-result.json"))
}
print("Swift application contract executed")
EOF
(cd /tmp && swift run --package-path "$consumer" Consumer "$repo/fixtures/application-integration" "$out" >/dev/null)
for expected in $(find "$repo/fixtures/application-integration" -name expected-result.json | sort); do
  relative=${expected#"$repo/fixtures/application-integration/"}
  echo "Swift application parity: ${relative%expected-result.json}"
  python3 "$repo/tools/compare_canonical_json.py" "$expected" "$out/${relative%expected-result.json}actual-result.json"
done
echo "Python↔Swift application parity passed"
