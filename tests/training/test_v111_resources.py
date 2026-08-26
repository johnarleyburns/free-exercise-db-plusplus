"""v1.11 cross-language resource and deterministic-resolution contracts."""

import hashlib
import json
from pathlib import Path

from fedbpp import resolve_intent


ROOT = Path(__file__).parents[2]


def test_canonical_intent_resources_are_byte_identical():
    resources = [
        ROOT / "resources/intent-policies.json",
        ROOT / "packages/python/fedbpp/data/intent-policies.json",
        ROOT / "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources/intent-policies.json",
        ROOT / "packages/kotlin/fedbpp/fedbpp/src/main/resources/intent-policies.json",
        ROOT / "packages/r/fedbpp/inst/extdata/intent-policies.json",
    ]
    digests = {hashlib.sha256(path.read_bytes()).hexdigest() for path in resources}
    assert len(digests) == 1


def test_canonical_intent_schema_is_packaged_for_native_languages():
    schema = json.loads((ROOT / "workout-intent.schema.json").read_text())
    for relative in (
        "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources/workout-intent.schema.json",
        "packages/kotlin/fedbpp/fedbpp/src/main/resources/workout-intent.schema.json",
        "packages/r/fedbpp/inst/extdata/workout-intent.schema.json",
    ):
        assert json.loads((ROOT / relative).read_text()) == schema


def test_repeated_resolution_is_deterministic():
    intent = json.loads((ROOT / "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json").read_text())
    db = {"metadata": {}, "exercises": {}}
    assert resolve_intent(intent, db) == resolve_intent(intent, db)
