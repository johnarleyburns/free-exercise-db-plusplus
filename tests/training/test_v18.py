"""v1.8 deterministic PLAN-generation regression tests."""
from __future__ import annotations

from fedbpp import Database, generate_plan, evaluate_plan


def db(order=("alpha_press", "beta_press", "row")):
    rows = {
        "alpha_press": {"source": {"name": "Alpha Press", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
        "beta_press": {"source": {"name": "Beta Press", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
        "row": {"source": {"name": "Row", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["back"], "indirect": ["biceps"], "stabilizers": [], "patterns": ["horizontal_pull"]}},
        "cable": {"source": {"name": "Cable", "equipment": "cable"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
    }
    keys = list(order) + ["cable"]
    return Database({"metadata": {"schemaVersion": "1", "converterVersion": "1", "setCredits": {"direct": 1, "indirect": .5, "stabilizer": 0}, "muscleOntology": ["chest", "back", "biceps"]}, "exercises": {key: rows[key] for key in keys}})


def profile(**extra):
    value = {"schemaVersion": "0.1.0", "profileId": "p", "availability": {"cycleLengthDays": 8, "sessionsPerCycle": {"min": 2, "target": 2, "max": 2}}, "equipment": ["body only"]}
    value.update(extra); return value


def target(**extra):
    value = {"schemaVersion": "0.1.0", "targetId": "t", "periodDays": 8, "muscles": {"chest": {"min": 2}}, "frequency": {"muscles": {"chest": {"min": 1}}}}
    value.update(extra); return value


def test_generation_is_deterministic_schema_valid_and_evaluator_parity():
    result = generate_plan(profile(), target(), db())
    repeat = generate_plan(profile(), target(), db())
    assert result["status"] == "generated"
    assert result == repeat
    assert len(result["plan"]["sessions"]) == 2
    assert result["plan"]["cycle"]["lengthDays"] == 8
    assert result["evaluation"] == evaluate_plan(result["plan"], db(), profile(), target())


def test_db_order_and_preference_do_not_change_implicit_ordering():
    p = profile(exercisePreferences={"preferredExerciseIds": ["beta_press"]})
    one = generate_plan(p, target(), db())
    two = generate_plan(p, target(), db(("row", "beta_press", "alpha_press")))
    assert one["plan"] == two["plan"]
    assert {x["exerciseId"] for s in one["plan"]["sessions"] for x in s["exercises"]} == {"beta_press"}


def test_required_unavailable_exercise_is_explicitly_unsatisfiable():
    result = generate_plan(profile(), target(), db(), requiredExerciseIds=["cable"])
    assert result["status"] == "unsatisfiable"
    assert result["unsatisfiedConstraints"] == [{"code": "NO_AVAILABLE_EQUIPMENT", "exerciseId": "cable"}]


def test_frequency_and_pattern_targets_are_distributed_and_satisfied():
    t = target(movementPatterns={"horizontal_push": {"minimumSets": 2}}, frequency={"muscles": {"chest": {"min": 1}}})
    result = generate_plan(profile(), t, db())
    assert result["status"] == "generated"
    assert result["evaluation"]["movementPatterns"]["horizontal_push"]["state"] != "below_minimum"
