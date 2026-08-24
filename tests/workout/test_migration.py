import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from src.workout.migrate_workout import migrate, migrate_to_02, migrate_to_03

ROOT = Path(__file__).parents[2]
SCHEMA = json.loads((ROOT / "workout.schema.json").read_text())

def base_workout(version="0.2.0"):
    return {"schemaVersion":version,"sessionId":"s","startTime":"2026-01-01T00:00:00Z","exercises":[{"exerciseId":"x","order":1,"sets":[{"setNumber":1,"setType":"working","completed":True}]}]}

def test_plan_linked_actual_is_valid():
    document=json.loads((ROOT / "examples/workouts/plan-linked.json").read_text())
    assert not list(Draft202012Validator(SCHEMA).iter_errors(document))
    assert document["planReference"]["revisionId"] == "basic-upper-lower-r1"
    assert document["exercises"][1]["substitution"]["reason"] == "equipment unavailable"

def test_standalone_02_remains_valid_and_migrates_without_links():
    original=base_workout(); migrated=migrate_to_03(original)
    assert original["schemaVersion"] == "0.2.0"
    assert migrated["schemaVersion"] == "0.3.0"
    assert "planReference" not in migrated
    assert migrated["exercises"] == original["exercises"]
    assert not list(Draft202012Validator(SCHEMA).iter_errors(migrated))

def test_01_to_03_is_forward_and_non_destructive():
    old=base_workout("0.1.0"); old["exercises"][0]["sets"][0]["repetitions"]=[{"repNumber":1,"velocity":{"value":1,"unit":"m/s"}}]
    result=migrate(old)
    assert result["schemaVersion"] == "0.3.0"
    assert result["exercises"][0]["laterality"] == "unspecified"
    assert result["exercises"][0]["sets"][0]["repetitions"][0]["meanVelocity"] == {"value":1,"unit":"m/s"}
    assert old["schemaVersion"] == "0.1.0"

def test_target_02_is_available_for_legacy_consumers():
    assert migrate(base_workout("0.1.0"), target_version="0.2.0")["schemaVersion"] == "0.2.0"
