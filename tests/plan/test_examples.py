import json
from pathlib import Path
import sys
import json

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from src.plan.validate_plan import semantic_errors, validate_plan

def test_all_dbpp_exercise_references_resolve():
    database = json.loads((ROOT / "free-exercise-db-plusplus.json").read_text())["exercises"]
    for path in sorted((ROOT / "examples/plans").glob("*.json")):
        plan = json.loads(path.read_text())
        for session in plan.get("sessions", []):
            for prescription in session.get("exercises", []):
                exercise_id = prescription.get("exerciseId")
                if exercise_id is not None:
                    assert exercise_id in database, f"{path}: {exercise_id}"


def test_valid_examples_pass_deterministic_validation():
    for path in sorted((ROOT / "examples/plans").glob("*.json")):
        plan = json.loads(path.read_text())
        assert validate_plan(plan) == [], path

def test_reversed_range_is_rejected_semantically():
    plan = json.loads((ROOT / "fixtures/plan/invalid/reversed-range.json").read_text())
    assert any("min must not exceed max" in error for error in semantic_errors(plan))

def test_duplicate_ids_are_rejected():
    plan = json.loads((ROOT / "examples/plans/basic-upper-lower.json").read_text())
    plan["sessions"][1]["planSessionId"] = plan["sessions"][0]["planSessionId"]
    assert any("duplicate ID" in error for error in semantic_errors(plan))


def test_plan_02_phase_and_planned_set_example_passes():
    plan = json.loads((ROOT / "examples/plans/periodized-0.2.json").read_text())
    assert validate_plan(plan) == []

def test_phase_and_set_ids_are_semantically_validated():
    plan = json.loads((ROOT / "fixtures/plan/invalid/unknown-phase-and-duplicate-set.json").read_text())
    errors = semantic_errors(plan)
    assert any("unknown phase" in error for error in errors)
    assert any("duplicate ID" in error for error in errors)
