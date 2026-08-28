#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
resources="$repo/packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources"

python3 - "$repo" "$resources" <<'PY'
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
resources = Path(sys.argv[2])
stable = [
    ("exercise-relationships.json", "exercise-relationships.json"),
    ("resources/intent-policies.json", "intent-policies.json"),
    ("workout.schema.json", "workout.schema.json"),
    ("workout-plan.schema.json", "workout-plan.schema.json"),
    ("volume-target.schema.json", "volume-target.schema.json"),
    ("training-profile.schema.json", "training-profile.schema.json"),
    ("workout-intent.schema.json", "workout-intent.schema.json"),
    ("coach-decision.schema.json", "coach-decision.schema.json"),
]
for canonical, packaged in stable:
    if (repo / canonical).read_bytes() != (resources / packaged).read_bytes():
        raise SystemExit(f"stable Swift resource differs: {repo / canonical} {resources / packaged}")

# The DB build stamps only metadata.generatedAt on each regeneration. Compare
# the canonical and bundled DB semantically while excluding that volatile field.
def database_without_build_stamp(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    value["metadata"].pop("generatedAt", None)
    return value

if database_without_build_stamp(repo / "free-exercise-db-plusplus.json") != database_without_build_stamp(resources / "free-exercise-db-plusplus.json"):
    raise SystemExit("Swift database resource differs after excluding metadata.generatedAt")
PY

size=$(find "$resources" -type f -printf '%s\n' | awk '{ total += $1 } END { print total + 0 }')
printf 'Swift production resource footprint: %s bytes (%s files)\n' "$size" "$(find "$resources" -type f | wc -l)"
echo "Swift canonical resource integrity ok"
