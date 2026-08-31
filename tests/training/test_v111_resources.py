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
        "packages/python/fedbpp/schemas/workout-intent.schema.json",
        "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources/workout-intent.schema.json",
        "packages/kotlin/fedbpp/fedbpp/src/main/resources/workout-intent.schema.json",
        "packages/r/fedbpp/inst/extdata/workout-intent.schema.json",
    ):
        assert json.loads((ROOT / relative).read_text()) == schema


def test_canonical_profile_schema_is_packaged_where_supported():
    schema = json.loads((ROOT / "training-profile.schema.json").read_text())
    for relative in (
        "packages/python/fedbpp/schemas/training-profile.schema.json",
        "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/Resources/training-profile.schema.json",
    ):
        assert json.loads((ROOT / relative).read_text()) == schema


def test_goal_contract_schemas_share_current_identity_and_vocabulary():
    intent_schema = json.loads((ROOT / "workout-intent.schema.json").read_text())
    profile_schema = json.loads((ROOT / "training-profile.schema.json").read_text())
    assert intent_schema["properties"]["schemaVersion"]["const"] == "0.2.0"
    assert profile_schema["properties"]["schemaVersion"]["const"] == "0.2.0"
    assert intent_schema["properties"]["goal"]["enum"] == profile_schema["$defs"]["goal"]["properties"]["type"]["enum"]
    assert {"endurance", "muscular_endurance"}.issubset(intent_schema["properties"]["goal"]["enum"])


def test_repeated_resolution_is_deterministic():
    intent = json.loads((ROOT / "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json").read_text())
    db = {"metadata": {}, "exercises": {}}
    assert resolve_intent(intent, db) == resolve_intent(intent, db)


def test_goal_policy_evidence_resolves_in_embedded_registry():
    policies = json.loads((ROOT / "resources/intent-policies.json").read_text())
    database = json.loads((ROOT / "free-exercise-db-plusplus.json").read_text())
    references = database["metadata"]["evidence"]["references"]
    expected_ids = {"repetition_continuum_2021", "rir_rpe_scale_2016"}
    for policy in policies["goalPolicies"].values():
        evidence = policy["evidence"]
        assert evidence["status"] != "provisional"
        assert set(evidence["references"]) == expected_ids
        assert all(reference in references for reference in evidence["references"])
