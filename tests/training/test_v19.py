"""v1.9 adaptive-coaching golden contracts."""
from __future__ import annotations

from copy import deepcopy

from fedbpp import Database, TrainingHistory, adapt_plan, evaluate_plan
from fedbpp.coaching import _worsens_target_excess


DB = Database({"metadata": {"schemaVersion": "db", "converterVersion": "c", "upstream": {"sha256": "a" * 64},
                           "setCredits": {"direct": 1, "indirect": .5, "stabilizer": 0}},
               "exercises": {"press": {"source": {"name": "Press", "equipment": "body only"},
                                       "annotation": {"direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"], "volumeEligible": True}},
                             "cable_press": {"source": {"name": "Cable Press", "equipment": "cable"},
                                             "annotation": {"direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"], "volumeEligible": True}},
                             "alternate_press": {"source": {"name": "Alternate Press", "equipment": "body only"},
                                                 "annotation": {"direct": ["chest"], "indirect": [], "stabilizers": [], "patterns": ["horizontal_push"], "volumeEligible": True}}}})
PROFILE = {"schemaVersion": "0.1.0", "profileId": "profile", "availability": {"cycleLengthDays": 8, "sessionsPerCycle": {"min": 1, "target": 1, "max": 2}}, "equipment": ["body only"]}
TARGET = {"schemaVersion": "0.1.0", "targetId": "target", "periodDays": 8, "muscles": {"chest": {"min": 2, "max": 6}}}
PLAN = {"schemaVersion": "0.2.0", "planId": "plan", "revisionId": "r1", "name": "Current", "cycle": {"lengthDays": 8},
        "sessions": [{"planSessionId": "session", "dayOffset": 0, "exercises": [{"prescriptionId": "press-rx", "exerciseId": "press", "order": 1, "sets": 2, "reps": {"min": 8, "max": 10}, "load": {"value": 100, "unit": "kg"}}]}]}


def _actual(day: str, session_id: str, reps=(10, 10)):
    return {"schemaVersion": "0.3.0", "sessionId": session_id, "startTime": day + "T12:00:00Z",
            "planReference": {"planId": "plan", "revisionId": "r1", "planSessionId": "session"},
            "exercises": [{"exerciseId": "press", "exercisePrescriptionId": "press-rx",
                           "sets": [{"setNumber": i + 1, "setType": "working", "completed": True, "reps": rep, "load": {"value": 100, "unit": "kg"}} for i, rep in enumerate(reps)]}]}


def _history(*workouts):
    return TrainingHistory("subject", [PLAN], list(workouts), plan_activations=[{"planId": "plan", "revisionId": "r1", "effectiveFrom": "2026-08-01T00:00:00Z"}])


def test_progression_is_a_deterministic_immutable_evaluator_gated_proposal():
    history = _history(_actual("2026-08-10", "a"), _actual("2026-08-18", "b"))
    one = adapt_plan(PROFILE, TARGET, PLAN, history, DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    two = adapt_plan(PROFILE, TARGET, PLAN, history, DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert one == two and one["status"] == "revision_proposed"
    assert PLAN["revisionId"] == "r1" and one["proposedPlan"]["revisionId"] == "r2"
    assert one["proposedPlan"]["sessions"][0]["exercises"][0]["load"]["value"] == 102.5
    assert one["proposedEvaluation"] == evaluate_plan(one["proposedPlan"], DB, PROFILE, TARGET)
    assert one["changes"][0]["type"] == "LOAD_CHANGED"


def test_hold_and_sparse_history_do_not_churn_revisions():
    hold = adapt_plan(PROFILE, TARGET, PLAN, _history(_actual("2026-08-18", "a", (9, 9))), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert hold["status"] == "no_change" and hold["proposedPlan"] is None
    sparse = adapt_plan(PROFILE, TARGET, PLAN, _history(), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert sparse["status"] == "insufficient_data" and sparse["proposedPlan"] is None


def test_repeated_failure_regresses_once_and_future_actual_is_excluded():
    history = _history(_actual("2026-08-10", "a", (7, 7)), _actual("2026-08-18", "b", (7, 7)), _actual("2026-09-01", "future", (10, 10)))
    result = adapt_plan(PROFILE, TARGET, PLAN, history, DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert result["status"] == "revision_proposed"
    assert result["proposedPlan"]["sessions"][0]["exercises"][0]["load"]["value"] == 97.5
    assert "REPEATED_PERFORMANCE_FAILURE" in result["decisions"][0]["reasonCodes"]


def test_equipment_drift_reuses_generation_and_never_returns_invalid_current_plan():
    profile = deepcopy(PROFILE); profile["equipment"] = ["cable"]
    result = adapt_plan(profile, TARGET, PLAN, _history(_actual("2026-08-18", "a")), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert result["status"] in {"regeneration_proposed", "unsatisfiable"}
    assert result["status"] != "no_change"


def test_explicit_repeated_substitution_is_the_only_substitution_signal():
    workouts = [_actual("2026-08-10", "a"), _actual("2026-08-18", "b")]
    for workout in workouts:
        actual = workout["exercises"][0]; actual["exerciseId"] = "alternate_press"
        actual["substitution"] = {"plannedPrescriptionId": "press-rx", "reason": "equipment"}
    result = adapt_plan(PROFILE, TARGET, PLAN, _history(*workouts), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert result["status"] == "revision_proposed"
    assert result["proposedPlan"]["sessions"][0]["exercises"][0]["exerciseId"] == "alternate_press"
    assert any(d["decisionType"] == "substitute_exercise" for d in result["decisions"])


def test_substitution_evidence_obeys_state_window_and_as_of():
    def substituted(day, sid):
        w = _actual(day, sid); actual = w["exercises"][0]
        actual["exerciseId"] = "alternate_press"; actual["substitution"] = {"plannedPrescriptionId": "press-rx", "reason": "equipment"}
        return w
    valid = [substituted("2026-08-10", "a"), substituted("2026-08-18", "b")]
    base = adapt_plan(PROFILE, TARGET, PLAN, _history(*valid), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    future = adapt_plan(PROFILE, TARGET, PLAN, _history(valid[0], substituted("2026-09-01", "future")), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    stale = adapt_plan(PROFILE, TARGET, PLAN, _history(valid[0], substituted("2026-06-01", "old")), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert base["status"] == "revision_proposed"
    assert future["status"] != "revision_proposed" and stale["status"] != "revision_proposed"
    evidence = next(d["evidence"] for d in base["decisions"] if d["decisionType"] == "substitute_exercise")
    assert evidence["sessionIds"] == ["a", "b"]


def test_target_maximum_gate_compares_excess_magnitude_and_ignores_missing_maximum():
    def evaluation(chest, maximum):
        return {"muscleCoverage": {"chest": {"actualEffectiveSets": chest, "maximum": maximum}},
                "frequency": {}, "movementPatterns": {}, "families": {"targets": {}}}
    assert _worsens_target_excess(evaluation(13, 12), evaluation(14, 12))
    assert not _worsens_target_excess(evaluation(14, 12), evaluation(13, 12))
    assert _worsens_target_excess(evaluation(12, 12), evaluation(13, 12))
    assert not _worsens_target_excess(evaluation(13, None), evaluation(20, None))


def test_unrepairable_target_drift_is_a_generator_backed_proposal_not_no_change():
    target = deepcopy(TARGET); target["muscles"]["back"] = {"min": 1}
    result = adapt_plan(PROFILE, target, PLAN, _history(_actual("2026-08-18", "a", (9, 9))), DB, options={"asOf": "2026-08-20T12:00:00Z", "timezone": "UTC"})
    assert result["status"] == "regeneration_proposed"
    assert result["proposedPlan"]["revisionId"] == "r2"
