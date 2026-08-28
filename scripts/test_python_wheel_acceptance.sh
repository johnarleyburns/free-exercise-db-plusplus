#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
wheel_dir=$(mktemp -d)
venv_dir=$(mktemp -d)
out_dir=$(mktemp -d)
trap 'rm -rf "$wheel_dir" "$venv_dir" "$out_dir"' EXIT

python3 -m pip wheel --no-deps --no-build-isolation "$repo/packages/python" -w "$wheel_dir" >/dev/null
python3 -m venv "$venv_dir"
"$venv_dir/bin/pip" install --quiet "$wheel_dir"/*.whl

cd "$out_dir"
REPO_ROOT="$repo" OUT_DIR="$out_dir" "$venv_dir/bin/python" - <<'PY'
import json
import os
from pathlib import Path

import fedbpp
from fedbpp import Database, RelationshipRegistry, TrainingHistory, WorkoutIntent

repo = Path(os.environ["REPO_ROOT"])
out = Path(os.environ["OUT_DIR"])
assert str(Path(fedbpp.__file__).resolve()).startswith(str(Path(sys_prefix := os.sys.prefix).resolve()))
assert repo not in Path(fedbpp.__file__).resolve().parents

def read(path):
    return json.loads(path.read_text())

db = Database.load(repo / "free-exercise-db-plusplus.json")
relationships = RelationshipRegistry.load(repo / "exercise-relationships.json", db=db)

evaluation = read(repo / "fixtures/cross-language/evaluation/input.json")
evaluation_result = fedbpp.evaluate_plan(evaluation["plan"], db, evaluation["profile"], evaluation["target"], relationships)
(out / "evaluation.json").write_text(json.dumps(evaluation_result, sort_keys=True))

history_doc = read(repo / "fixtures/cross-language/history/input.json")
history = TrainingHistory(history_doc["subjectId"], history_doc["plans"], history_doc["workouts"], history_doc["targets"], history_doc["planActivations"])
state = fedbpp.derive_training_state(history, db, as_of=history_doc["asOf"], window=history_doc["window"], timezone=history_doc["timezone"], relationships=relationships)
(out / "history.json").write_text(json.dumps(state, sort_keys=True))

generation = read(repo / "fixtures/cross-language/generation/input.json")
generated = fedbpp.generate_plan(generation["profile"], generation["target"], db, policy=generation["policy"], relationships=relationships, requiredExerciseIds=generation["requiredExerciseIds"])
(out / "generation.json").write_text(json.dumps(generated, sort_keys=True))

adaptation = read(repo / "fixtures/cross-language/adaptation/input.json")
adaptation_history = adaptation["history"]
adaptation_history_obj = TrainingHistory(adaptation_history["subjectId"], adaptation_history["plans"], adaptation_history["workouts"], adaptation_history["targets"], adaptation_history["planActivations"])
adapted = fedbpp.adapt_plan(adaptation["profile"], adaptation["target"], adaptation["currentPlan"], adaptation_history_obj, db, policy=adaptation["policy"], relationships=relationships, options={"asOf": adaptation["asOf"]})
(out / "adaptation.json").write_text(json.dumps(adapted, sort_keys=True))

intent_doc = read(repo / "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")
intent = WorkoutIntent.from_dict(intent_doc, validate=False)
resolution = fedbpp.resolve_intent(intent, db)
(out / "intent-resolution.json").write_text(json.dumps(resolution, sort_keys=True))
intent_generation = fedbpp.generate_plan_from_intent(intent_doc, db)
(out / "intent-generation.json").write_text(json.dumps(intent_generation, sort_keys=True))
print("python wheel imports and API smoke ok")
PY

python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/evaluation/expected.json" "$out_dir/evaluation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/history/expected.json" "$out_dir/history.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/generation/expected.json" "$out_dir/generation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/adaptation/expected.json" "$out_dir/adaptation.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-resolution.json" "$out_dir/intent-resolution.json"
python3 "$repo/tools/compare_canonical_json.py" "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/expected-generation.json" "$out_dir/intent-generation.json"
echo "python wheel goldens ok"
