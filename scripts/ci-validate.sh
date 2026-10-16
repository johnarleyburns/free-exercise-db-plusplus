#!/usr/bin/env bash
# Single source of truth for PR validation. Used by the PR validation workflow,
# the issue agent and the repair agent so the three cannot drift.
set -euo pipefail
cd "${CI_VALIDATE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

step() { echo "::group::$*"; echo "=== $* ==="; }
endstep() { echo "::endgroup::"; }

step "Shell syntax"
while IFS= read -r f; do
  bash -n "$f" || { echo "Shell syntax error: $f" >&2; exit 1; }
done < <(git ls-files '*.sh')
endstep

step "Workflow YAML"
while IFS= read -r f; do
  ruby -ryaml -e 'YAML.safe_load(File.read(ARGV[0]), aliases: true)' "$f" \
    || { echo "Invalid workflow YAML: $f" >&2; exit 1; }
done < <(git ls-files '.github/workflows/*.yml')
endstep

step "Automation regression tests"
if [[ -f scripts/tests/test-pr-maintenance.sh && -f .github/scripts/pr-maintenance.sh ]]; then
  bash scripts/tests/test-pr-maintenance.sh
fi
endstep

[[ "${1:-}" == "--fast" ]] && exit 0

step "Python validator and syntax"
python -m pip install --disable-pip-version-check jsonschema
python -m compileall -q src packages/python tools
endstep

step "Core database contracts"
python tests/test_release_contract.py free-exercise-db-plusplus.json
python tests/test_golden_mappings.py free-exercise-db-plusplus.json
python tests/test_medium_policy.py free-exercise-db-plusplus.json
endstep

step "Swift package and resource parity"
swift test
bash scripts/test_swift_resources.sh
endstep

step "Repository hygiene"
git diff --check
endstep
