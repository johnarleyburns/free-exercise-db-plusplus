"""v1.8 deterministic PLAN-generation regression tests."""
from __future__ import annotations

import pytest

from fedbpp import Database, PlanningPolicy, generate_plan, evaluate_plan


def db(order=("alpha_press", "beta_press", "row")):
    rows = {
        "alpha_press": {"source": {"name": "Alpha Press", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
        "beta_press": {"source": {"name": "Beta Press", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
        "row": {"source": {"name": "Row", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["back"], "indirect": ["biceps"], "stabilizers": [], "patterns": ["horizontal_pull"]}},
        "squat": {"source": {"name": "Squat", "equipment": "body only"}, "annotation": {"volumeEligible": True, "direct": ["quadriceps"], "indirect": ["glutes"], "stabilizers": [], "patterns": ["squat"]}},
        "cable": {"source": {"name": "Cable", "equipment": "cable"}, "annotation": {"volumeEligible": True, "direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"]}},
    }
    keys = list(order) + ["cable"]
    return Database({"metadata": {"schemaVersion": "1", "converterVersion": "1", "setCredits": {"direct": 1, "indirect": .5, "stabilizer": 0}, "muscleOntology": ["chest", "back", "biceps", "quadriceps", "glutes"]}, "exercises": {key: rows[key] for key in keys}})


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
    assert result["plan"] == {
        "schemaVersion": "0.2.0", "planId": "generated-plan", "revisionId": "r1",
        "name": "Generated full-body-general-v1", "description": None, "cycle": {"lengthDays": 8},
        "sessions": [
            {"planSessionId": "session-1", "dayOffset": 0, "name": "Session 1", "exercises": [{"prescriptionId": "rx-01-01", "exerciseId": "alpha_press", "exerciseName": "Alpha Press", "order": 1, "sets": 1, "reps": {"min": 6, "target": 8, "max": 10}, "effort": {"rir": 2}, "setType": "working"}]},
            {"planSessionId": "session-2", "dayOffset": 4, "name": "Session 2", "exercises": [{"prescriptionId": "rx-02-01", "exerciseId": "alpha_press", "exerciseName": "Alpha Press", "order": 1, "sets": 1, "reps": {"min": 6, "target": 8, "max": 10}, "effort": {"rir": 2}, "setType": "working"}]},
        ],
    }


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


def test_zero_session_range_and_invalid_policy_are_explicit_failures():
    p = profile(availability={"cycleLengthDays": 8, "sessionsPerCycle": {"max": 0}}, equipment=["body only"])
    result = generate_plan(p, target(), db())
    assert result["status"] == "unsatisfiable"
    assert result["unsatisfiedConstraints"][0]["code"] == "SESSION_COUNT_CONFLICT"
    policy = PlanningPolicy("bad", "1", "bad", "upper_lower", "x", "x", "x", "x", {})
    with pytest.raises(ValueError, match="invalid planning policy configuration"):
        generate_plan(profile(), target(), db(), policy=policy)


def test_custom_set_credits_and_history_continuity_are_authoritative():
    document = db()._document
    document["metadata"]["setCredits"] = {"direct": .5, "indirect": .25, "stabilizer": 0}
    credited = Database(document)
    result = generate_plan(profile(), target(), credited)
    assert sum(rx["sets"] for session in result["plan"]["sessions"] for rx in session["exercises"] if rx["exerciseId"] == "alpha_press") == 4
    state = {"stateVersion": "0.1.0", "exerciseState": {"beta_press": {"recentPerformances": [{"startedAt": "2026-01-01T00:00:00Z"}], "prescriptionAdherence": {"setAdherence": 1.0}}}}
    continued = generate_plan(profile(), target(), db(), training_state=state)
    assert {rx["exerciseId"] for session in continued["plan"]["sessions"] for rx in session["exercises"]} == {"beta_press"}


def test_family_target_without_relationships_is_invalid_input():
    result = generate_plan(profile(), target(families={"press": {"minimumSets": 1}}), db())
    assert result["status"] == "invalid_input"
    assert any("family targets require" in row["detail"] for row in result["unsatisfiedConstraints"])


def current_plan(exercise_id="alpha_press", day_offset=4):
    return {"schemaVersion": "0.2.0", "planId": "current", "revisionId": "r1", "name": "Current", "cycle": {"lengthDays": 8}, "sessions": [
        {"planSessionId": "current-1", "dayOffset": 0, "exercises": [{"prescriptionId": "old-1", "exerciseId": "row", "order": 1, "sets": 1, "reps": 8}]},
        {"planSessionId": "current-2", "dayOffset": day_offset, "exercises": [{"prescriptionId": "old-2", "exerciseId": exercise_id, "order": 1, "sets": 1, "reps": 8}]},
    ]}


def test_locked_exercise_preserves_current_plan_day_offset_and_reports_conflicts():
    locked = generate_plan(profile(), target(), db(), current_plan=current_plan(), lockedExerciseIds=["alpha_press"])
    assert locked["status"] == "generated"
    assert any(rx["exerciseId"] == "alpha_press" for session in locked["plan"]["sessions"] if session["dayOffset"] == 4 for rx in session["exercises"])
    excluded = generate_plan(profile(constraints={"excludedExerciseIds": ["alpha_press"]}), target(), db(), current_plan=current_plan(), lockedExerciseIds=["alpha_press"])
    assert excluded["status"] == "unsatisfiable" and excluded["unsatisfiedConstraints"][0]["code"] == "LOCKED_EXERCISE_CONFLICT"
    unavailable = generate_plan(profile(), target(), db(), current_plan=current_plan("cable"), lockedExerciseIds=["cable"])
    assert unavailable["status"] == "unsatisfiable" and unavailable["unsatisfiedConstraints"][0]["code"] == "LOCKED_EXERCISE_CONFLICT"
    unavailable_day = generate_plan(profile(availability={"cycleLengthDays": 8, "sessionsPerCycle": {"min": 2, "target": 2, "max": 2}, "excludedDayOffsets": [4]}), target(), db(), current_plan=current_plan(), lockedExerciseIds=["alpha_press"])
    assert unavailable_day["status"] == "unsatisfiable" and unavailable_day["unsatisfiedConstraints"][0]["code"] == "LOCKED_EXERCISE_CONFLICT"


def test_upper_lower_policy_is_deterministic_and_uses_explicit_metadata_partition():
    p = profile(availability={"cycleLengthDays": 8, "sessionsPerCycle": {"min": 4, "target": 4, "max": 4}}, equipment=["body only"])
    t = target(muscles={"chest": {"min": 2}, "quadriceps": {"min": 2}})
    result = generate_plan(p, t, db(("alpha_press", "beta_press", "row", "squat")), policy="upper-lower-general-v1")
    assert result["status"] == "generated" and result == generate_plan(p, t, db(("squat", "row", "beta_press", "alpha_press")), policy="upper-lower-general-v1")
    assert [session["name"] for session in result["plan"]["sessions"]] == ["Upper 1", "Lower 1", "Upper 2", "Lower 2"]
    assert all(rx["exerciseId"] != "squat" for session in result["plan"]["sessions"][::2] for rx in session["exercises"])
    assert all(rx["exerciseId"] == "squat" for session in result["plan"]["sessions"][1::2] for rx in session["exercises"])
