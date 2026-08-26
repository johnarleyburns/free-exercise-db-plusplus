from __future__ import annotations

import json
from pathlib import Path

from fedbpp import Database, TrainingHistory, evaluate_plan, generate_plan_from_intent, resolve_intent
from fedbpp.intent import ENVIRONMENT_POLICIES, GOAL_POLICIES, validate_workout_intent


def db():
    return Database({"metadata": {"schemaVersion": "1", "converterVersion": "1", "setCredits": {"direct": 1, "indirect": .5, "stabilizer": 0}}, "exercises": {
        "press": {"source": {"name": "Press", "equipment": "dumbbell"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_press"]}},
        "row": {"source": {"name": "Row", "equipment": "dumbbell"}, "annotation": {"volumeEligible": True, "direct": ["lats"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_pull"]}},
        "squat": {"source": {"name": "Squat", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["quadriceps"], "indirect": [], "stabilizers": [], "patterns": ["squat"]}},
        "hinge": {"source": {"name": "Hinge", "equipment": "barbell"}, "annotation": {"volumeEligible": True, "direct": ["hamstrings"], "indirect": [], "stabilizers": [], "patterns": ["hip_hinge"]}},
    }})

def intent(**changes):
    value = {"schemaVersion": "0.1.0", "goal": "hypertrophy", "schedule": {"cycleLengthDays": 7, "sessionsPerCycle": {"min": 5, "target": 5, "max": 5}, "preferredWeekdays": ["monday", "tuesday", "wednesday", "thursday", "saturday"]}, "sessionConstraints": {"exercisesPerSession": {"min": 3, "max": 4}}, "environment": "commercial_gym"}
    value.update(changes); return value

def test_flagship_is_deterministic_and_enforces_counts():
    one = generate_plan_from_intent(intent(), db()); two = generate_plan_from_intent(intent(), db())
    assert one == two and one["resolution"]["goalPolicy"]["policyId"] == "general-hypertrophy-v1"
    assert one["resolution"]["environmentPolicy"] == "commercial-gym-general-v1"
    assert [s["dayOffset"] for s in one["generation"]["plan"]["sessions"]] == [0, 1, 2, 3, 5]
    assert all(3 <= len(s["exercises"]) <= 4 for s in one["generation"]["plan"]["sessions"])
    assert one["generation"]["evaluation"]["summary"]["satisfiesHardConstraints"]

def test_nonseven_weekdays_and_conflicts_are_invalid():
    assert resolve_intent(intent(schedule={"cycleLengthDays": 8, "sessionsPerCycle": {"target": 2}, "preferredWeekdays": ["monday"]}), db())["status"] == "invalid"
    assert resolve_intent(intent(exerciseConstraints={"requiredExerciseIds": ["press"], "excludedExerciseIds": ["press"]}), db())["status"] == "invalid"

def test_partial_ranges_and_evaluator_hard_bounds():
    r = resolve_intent(intent(schedule={"cycleLengthDays": 7, "sessionsPerCycle": {"min": 2}}, sessionConstraints={"exercisesPerSession": {"min": 3}}), db())
    assert r["resolvedProfile"]["availability"]["sessionsPerCycle"] == {"min": 2}
    profile = r["resolvedProfile"]; profile["availability"]["exercisesPerSession"] = {"min": 3, "max": 4}
    plan = {"schemaVersion": "0.2.0", "planId": "p", "revisionId": "r", "name": "p", "cycle": {"lengthDays": 7}, "sessions": [{"planSessionId": "s", "dayOffset": 0, "exercises": [{"prescriptionId": "x", "exerciseId": "press", "order": 1, "sets": 1, "reps": 8}]}]}
    result = evaluate_plan(plan, db(), profile, r["resolvedTarget"])
    assert result["exerciseCounts"]["s"]["state"] == "below_minimum"
    assert not result["summary"]["satisfiesHardConstraints"]


def test_schema_privacy_policy_and_partial_range_contracts():
    # No identity or health information is required: opaque subjectId is optional too.
    value = intent()
    assert not validate_workout_intent(value, db())
    assert "name" not in json.loads(Path("workout-intent.schema.json").read_text())["properties"]
    assert ENVIRONMENT_POLICIES["commercial-gym-general-v1"]["equipment"] == (
        "bands", "barbell", "body only", "cable", "dumbbell", "e-z curl bar",
        "exercise ball", "kettlebells", "machine", "medicine ball",
    )
    assert ENVIRONMENT_POLICIES["bodyweight-only-v1"]["equipment"] == ("body only",)
    assert GOAL_POLICIES["general-hypertrophy-v1"]["muscles"]["chest"] == {"target": 6}
    assert GOAL_POLICIES["general-strength-v1"]["reps"] == {"min": 3, "target": 5, "max": 6}
    for rng in ({"min": 2}, {"target": 2}, {"max": 2}):
        assert resolve_intent(intent(schedule={"cycleLengthDays": 7, "sessionsPerCycle": rng}), db())["resolvedProfile"]["availability"]["sessionsPerCycle"] == rng


def test_conflicts_unknowns_and_environment_override_contracts():
    cases = [
        intent(preferences={"preferredExerciseIds": ["press"]}, exerciseConstraints={"excludedExerciseIds": ["press"]}),
        intent(schedule={"cycleLengthDays": 7, "sessionsPerCycle": {"target": 5, "max": 4}}),
        intent(sessionConstraints={"exercisesPerSession": {"min": 4, "max": 3}}),
        intent(environment="custom", equipmentOverrides={}),
        intent(exerciseConstraints={"requiredExerciseIds": ["unknown"]}),
        intent(requestedGoalPolicy="unknown-v1"),
        intent(requestedPlanningPolicy="unknown-v1"),
    ]
    assert all(resolve_intent(value, db())["status"] in {"invalid", "needs_clarification"} for value in cases)
    commercial = resolve_intent(intent(equipmentOverrides={"removeEquipment": ["barbell"]}), db())
    assert "barbell" not in commercial["resolvedProfile"]["equipment"]
    custom = resolve_intent(intent(environment="custom", equipmentOverrides={"addEquipment": ["dumbbell", "body only"]}), db())
    assert custom["environmentPolicy"] is None and custom["resolvedProfile"]["equipment"] == ["body only", "dumbbell"]
    assert resolve_intent(intent(environment="home_gym"), db())["status"] == "needs_clarification"


def test_exercise_count_hard_and_soft_states():
    profile = resolve_intent(intent(), db())["resolvedProfile"]
    target = resolve_intent(intent(), db())["resolvedTarget"]
    def plan(count):
        exercises = [{"prescriptionId": f"x{index}", "exerciseId": "press", "order": index + 1, "sets": 1, "reps": 8} for index in range(count)]
        return {"schemaVersion": "0.2.0", "planId": "p", "revisionId": "r", "name": "p", "cycle": {"lengthDays": 7}, "sessions": [{"planSessionId": "s", "dayOffset": 0, "exercises": exercises}]}
    for count, state, hard in ((2, "below_minimum", True), (3, "within_range", False), (4, "within_range", False), (5, "above_maximum", True)):
        evaluated = evaluate_plan(plan(count), db(), profile, target)
        assert evaluated["exerciseCounts"]["s"]["state"] == state
        assert (not evaluated["summary"]["satisfiesHardConstraints"]) is hard
    profile["availability"]["exercisesPerSession"] = {"min": 3, "target": 3, "max": 4}
    assert evaluate_plan(plan(4), db(), profile, target)["summary"]["softPreferenceWarnings"] >= 1


def test_cross_language_oracles_and_flagship_full_database():
    root = Path("fixtures/cross-language/intent")
    full_db = Database.load("free-exercise-db-plusplus.json")
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        value = json.loads((directory / "input.json").read_text())
        expected = json.loads((directory / "expected-resolution.json").read_text())
        if (directory / "history.json").exists():
            history_doc = json.loads((directory / "history.json").read_text())
            history = TrainingHistory(history_doc["subjectId"], history_doc["plans"], history_doc["workouts"], plan_activations=history_doc["planActivations"])
            assert resolve_intent(value, full_db, history=history, as_of="2026-08-25T12:00:00Z") == expected
        else:
            assert resolve_intent(value, full_db) == expected
    directory = root / "flagship-5day-hypertrophy"
    result = generate_plan_from_intent(json.loads((directory / "input.json").read_text()), full_db)
    assert result == json.loads((directory / "expected-generation.json").read_text())
    plan = result["generation"]["plan"]
    assert len(plan["sessions"]) == 5
    assert [session["dayOffset"] for session in plan["sessions"]] == [0, 1, 2, 3, 5]
    assert all(3 <= len(session["exercises"]) <= 4 for session in plan["sessions"])
    available = set(result["resolution"]["resolvedProfile"]["equipment"])
    assert all(full_db.get_exercise(rx["exerciseId"]).data["source"]["equipment"] in available for session in plan["sessions"] for rx in session["exercises"])


def test_history_is_derived_only_when_requested_with_explicit_as_of():
    plan = {"schemaVersion": "0.2.0", "planId": "p", "revisionId": "r", "cycle": {"lengthDays": 7}, "sessions": [{"planSessionId": "s", "dayOffset": 0, "exercises": [{"prescriptionId": "rx", "exerciseId": "press", "sets": 1, "reps": 8}]}]}
    actual = {"schemaVersion": "0.3.0", "sessionId": "w", "startTime": "2026-08-24T12:00:00Z", "planReference": {"planId": "p", "revisionId": "r", "planSessionId": "s"}, "exercises": [{"exerciseId": "press", "exercisePrescriptionId": "rx", "sets": [{"completed": True, "setType": "working", "reps": 8}]}]}
    history = TrainingHistory("subject", [plan], [actual], plan_activations=[{"planId": "p", "revisionId": "r", "effectiveFrom": "2026-08-01T00:00:00Z"}])
    historical = resolve_intent(intent(useHistory=True), db(), history=history, as_of="2026-08-25T12:00:00Z")
    assert historical["generationOptions"]["trainingState"]["exerciseState"]["press"]["recentSessionCount"] == 1
    no_history = resolve_intent(intent(useHistory=False), db(), history=history, as_of="2026-08-25T12:00:00Z")
    assert "trainingState" not in no_history["generationOptions"]
