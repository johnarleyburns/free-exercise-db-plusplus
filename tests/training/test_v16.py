import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[2]
import sys
sys.path.insert(0, str(ROOT / "packages/python"))
from fedbpp import Database, RelationshipRegistry, evaluate_plan, validate_training_profile

def load(path): return json.loads(Path(path).read_text())

def test_profile_schema_privacy_and_examples():
    schema = load(ROOT / "training-profile.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for path in sorted((ROOT / "examples/training-profiles").glob("*.json")):
        assert not list(validator.iter_errors(load(path))), path
    required = set(schema["required"])
    assert not required & {"name", "email", "phone", "address", "DOB", "medicalDiagnosis", "medicalRecordNumber"}

def test_profile_semantics_and_contradictions():
    db = Database.load(ROOT / "free-exercise-db-plusplus.json")
    profile = load(ROOT / "examples/training-profiles/excluded-exercise.json")
    assert validate_training_profile(profile, db) == []
    bad = copy.deepcopy(profile); bad["exercisePreferences"] = {"preferredExerciseIds": [profile["constraints"]["excludedExerciseIds"][0]]}
    assert any("contradictory" in e for e in validate_training_profile(bad, db))
    bad = copy.deepcopy(profile); bad["constraints"]["excludedExerciseIds"] = ["missing"]
    assert any("unknown exerciseId" in e for e in validate_training_profile(bad, db))

def test_golden_evaluation_is_deterministic_and_separates_findings():
    db = Database.load(ROOT / "free-exercise-db-plusplus.json")
    plan = {"schemaVersion":"0.1.0", "planId":"golden", "revisionId":"r1", "cycle":{"lengthDays":7}, "sessions":[
        {"planSessionId":"a", "dayOffset":0, "exercises":[
            {"prescriptionId":"bench-a", "exerciseId":"Barbell_Bench_Press_-_Medium_Grip", "order":1, "sets":6, "reps":8},
            {"prescriptionId":"cable-a", "exerciseId":"Cable_Chest_Press", "order":2, "sets":6, "reps":8}]},
        {"planSessionId":"b", "dayOffset":3, "exercises":[
            {"prescriptionId":"squat-b", "exerciseId":"Barbell_Squat", "order":1, "sets":4, "reps":8}]}
    ]}
    profile = load(ROOT / "examples/plan-evaluation/profile-golden.json")
    target = load(ROOT / "examples/plan-evaluation/golden-target.json")
    relationships = RelationshipRegistry.load(ROOT / "exercise-relationships.json", db=db)
    result = evaluate_plan(plan, db, profile, target, relationships)
    assert result["summary"]["hardConstraintViolations"] == 2
    assert result["summary"]["targetGaps"] == 3
    assert result["equipment"]["unsupportedExercises"][0]["exerciseId"] == "Cable_Chest_Press"
    assert any(row.get("exerciseId") == "Barbell_Squat" and row["type"] == "excluded_exercise" for row in result["constraints"]["violations"])
    assert result["frequency"]["chest"]["state"] == "below_minimum"
    assert result["movementPatterns"]["hinge"]["state"] == "below_minimum"
    assert result["provenance"]["setCredits"] == db.metadata["setCredits"]
    assert evaluate_plan(plan, db, profile, target, relationships) == result

def test_evaluation_without_target_or_relationships_still_works():
    db = Database.load(ROOT / "free-exercise-db-plusplus.json")
    result = evaluate_plan(load(ROOT / "examples/plans/push-pull-legs.json"), db)
    assert result["frequency"] == {} and result["families"]["coverage"]["available"] is False
