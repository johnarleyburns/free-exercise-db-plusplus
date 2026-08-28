#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python3 - "$repo/free-exercise-db-plusplus.json" "$repo/packages/kotlin/fedbpp/fedbpp/src/main/resources/free-exercise-db-plusplus.json" <<'PY'
import json
import sys

def stable(path):
    value = json.load(open(path, encoding="utf-8"))
    value.get("metadata", {}).pop("generatedAt", None)
    return value

assert stable(sys.argv[1]) == stable(sys.argv[2]), "Kotlin database resource differs semantically"
PY
cmp "$repo/exercise-relationships.json" "$repo/packages/kotlin/fedbpp/fedbpp/src/main/resources/exercise-relationships.json"
if rg -n 'android\.|androidx\.' "$repo/packages/kotlin/fedbpp/fedbpp/src/main/kotlin"; then
  echo "Android framework import found in semantic Kotlin core" >&2
  exit 1
fi
echo "Kotlin bundled resources and Android boundary are valid"
