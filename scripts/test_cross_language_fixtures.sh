#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
before=$(mktemp)
after=$(mktemp)
trap 'rm -f "$before" "$after"' EXIT

find "$repo/fixtures/cross-language" -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > "$before"
python3 "$repo/tools/generate_cross_language_engine_fixtures.py"
find "$repo/fixtures/cross-language" -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > "$after"
cmp "$before" "$after"
python3 "$repo/tools/compare_canonical_json.py" \
  "$repo/fixtures/cross-language/evaluation/expected.json" \
  "$repo/fixtures/cross-language/evaluation/expected.json"
echo "cross-language fixture regeneration ok"
