#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
resources="$repo/packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources"

declare -a pairs=(
  "free-exercise-db-plusplus.json|free-exercise-db-plusplus.json"
  "exercise-relationships.json|exercise-relationships.json"
  "resources/intent-policies.json|intent-policies.json"
  "workout.schema.json|workout.schema.json"
  "workout-plan.schema.json|workout-plan.schema.json"
  "volume-target.schema.json|volume-target.schema.json"
  "training-profile.schema.json|training-profile.schema.json"
  "workout-intent.schema.json|workout-intent.schema.json"
  "coach-decision.schema.json|coach-decision.schema.json"
)
for pair in "${pairs[@]}"; do
  IFS='|' read -r canonical packaged <<< "$pair"
  cmp "$repo/$canonical" "$resources/$packaged"
done

size=$(find "$resources" -type f -printf '%s\n' | awk '{ total += $1 } END { print total + 0 }')
printf 'Swift production resource footprint: %s bytes (%s files)\n' "$size" "$(find "$resources" -type f | wc -l)"
echo "Swift canonical resource integrity ok"
