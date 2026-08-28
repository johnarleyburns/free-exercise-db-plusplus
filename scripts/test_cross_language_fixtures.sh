#!/usr/bin/env bash
set -euo pipefail

# Fixture-regeneration validation only. Native language parity is tested by
# the language-specific parity scripts, including test_r_python_parity.sh.

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
before=$(mktemp)
after=$(mktemp)
trap 'rm -f "$before" "$after"' EXIT

find "$repo/fixtures/cross-language" -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > "$before"
python3 "$repo/tools/generate_cross_language_engine_fixtures.py"
find "$repo/fixtures/cross-language" -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > "$after"
cmp "$before" "$after"
echo "cross-language fixture regeneration ok"
