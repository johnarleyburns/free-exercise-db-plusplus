#!/usr/bin/env bash
set -euo pipefail

# Compare the Python facade with its own canonical application fixtures. The
# other language scripts consume these same expected-result.json documents.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHONPATH="$repo/packages/python" python3 - "$repo" <<'PY'
import json, sys
from pathlib import Path
from fedbpp import Database, RelationshipRegistry, TrainingRequest, process_training_request

root = Path(sys.argv[1])
db = Database.load(root / "free-exercise-db-plusplus.json")
relationships = RelationshipRegistry.load(root / "exercise-relationships.json")
for directory in sorted(p for p in (root / "fixtures/application-integration").iterdir() if p.is_dir()):
    request = TrainingRequest.load(directory / "request.json")
    actual = process_training_request(request, db, relationships)
    expected = json.loads((directory / "expected-result.json").read_text())
    if actual != expected:
        raise SystemExit(f"Python application parity mismatch: {directory.name}")
print("Python application contract parity passed")
PY
