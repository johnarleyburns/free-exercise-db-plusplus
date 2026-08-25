from contextlib import contextmanager

@contextmanager
def raises_value_error(text):
    try:
        yield
    except ValueError as exc:
        assert text in str(exc)
    else:
        raise AssertionError("expected ValueError")

from fedbpp import Database, TrainingHistory, analyze_cohort, analyze_periods


DB = Database({
    "metadata": {"schemaVersion": "test", "converterVersion": "test", "setCredits": {"direct": 1, "indirect": .5, "stabilizer": 0}},
    "exercises": {
        "upper": {"exerciseId": "upper", "annotation": {"direct": ["chest"], "indirect": ["triceps"], "stabilizers": [], "patterns": ["push"], "volumeEligible": True}},
        "back": {"exerciseId": "back", "annotation": {"direct": ["back"], "indirect": [], "stabilizers": [], "patterns": ["pull"], "volumeEligible": True}},
    },
})


def plan(revision="r1", effective_from=None, effective_to=None):
    value = {"schemaVersion": "0.2.0", "planId": "p", "revisionId": revision, "cycle": {"lengthDays": 7}, "sessions": [{"planSessionId": "upper", "dayOffset": 0, "exercises": [{"prescriptionId": "rx", "exerciseId": "upper", "sets": {"min": 3, "target": 4, "max": 5}, "reps": {"target": 8}}]}]}
    if effective_from: value["effectiveFrom"] = effective_from
    if effective_to: value["effectiveTo"] = effective_to
    return value


def workout(sid, day, *, revision="r1", reference=True, count=4, reps=8, exercise="upper"):
    value = {"schemaVersion": "0.3.0", "sessionId": sid, "startTime": f"{day}T12:00:00Z", "exercises": [{"exerciseId": exercise, "exercisePrescriptionId": "rx", "sets": [{"setNumber": n, "setType": "working", "completed": True, "reps": reps} for n in range(1, count + 1)]}]}
    if reference:
        value["planReference"] = {"planId": "p", "revisionId": revision, "planSessionId": "upper"}
    return value


def test_repeated_occurrences_are_independent_and_strictly_date_matched():
    history = TrainingHistory("S001", [plan()], [workout("w1", "2026-01-05"), workout("w3", "2026-01-19")])
    result = analyze_periods(history, DB, start="2026-01-05", end="2026-02-01", timezone="UTC")
    rows = result["sessionRows"]
    assert result["periods"][0]["scheduledPlannedSessions"] == 1
    assert sum(x["session_status"] == "matched" for x in rows) == 2
    missed = [x for x in rows if x["session_status"] == "missed_planned_session"]
    assert [x["scheduled_date"] for x in missed] == ["2026-01-12", "2026-01-26"]
    assert all(x["missed_sets_min"] == 3 and x["missed_sets_target"] == 4 and x["missed_sets_max"] == 5 for x in missed)


def test_revision_boundary_is_clipped_and_provenance_is_multi_revision():
    r1 = plan("r1", "2026-01-01T00:00:00Z", "2026-01-07T00:00:00Z")
    r2 = plan("r2", "2026-01-07T00:00:00Z")
    result = analyze_periods(TrainingHistory("S001", [r1, r2], [workout("w", "2026-01-05", revision="r1")]), DB, start="2026-01-05", end="2026-01-11", timezone="UTC")
    assert len(result["periods"]) == 1
    assert result["periods"][0]["planRevisionsUsed"] == ["r1", "r2"]
    assert {x["revision_id"] for x in result["sessionRows"] if x["session_status"] == "missed_planned_session"} == {"r2"}


def test_overlapping_activations_are_an_error():
    histories = TrainingHistory("S001", [plan("r1"), plan("r2")], [workout("w", "2026-01-07", reference=False)], plan_activations=[{"planId": "p", "revisionId": "r1", "effectiveFrom": "2026-01-01", "effectiveTo": "2026-01-10"}, {"planId": "p", "revisionId": "r2", "effectiveFrom": "2026-01-05", "effectiveTo": "2026-01-20"}])
    with raises_value_error("overlapping plan activation"):
        analyze_periods(histories, DB, start="2026-01-05", end="2026-01-11", timezone="UTC")


def test_exercise_adherence_and_substitution_reason_are_canonical_fields():
    actual = workout("w", "2026-01-05", count=3, reps=7)
    actual["exercises"][0]["substitution"] = {"plannedPrescriptionId": "rx", "reason": "equipment_unavailable"}
    result = analyze_periods(TrainingHistory("S001", [plan()], [actual]), DB, start="2026-01-05", end="2026-01-11", timezone="UTC")
    row = result["exerciseRows"][0]
    assert row["set_adherence"]["actual"] == 3
    assert row["reps_adherence"]["actual"] == 21
    assert row["substitution_reason"] == "equipment_unavailable"


def test_unplanned_unmapped_work_is_retained_and_exposure_is_session_based():
    actual = workout("w", "2026-01-05", reference=False)
    actual["exercises"].append({"exerciseId": "custom", "sets": [{"completed": True, "setType": "working"}]})
    result = analyze_periods(TrainingHistory("S001", [plan()], [actual]), DB, start="2026-01-05", end="2026-01-11", timezone="UTC")
    session = next(x for x in result["sessionRows"] if x["session_status"] == "unplanned_session")
    assert session["session_status"] == "unplanned_session"
    assert session["unplanned_sets"] == 5
    assert any(x["actual_exercise_id"] == "custom" and x["unmapped"] for x in result["exerciseRows"])
    chest = next(x for x in result["musclePeriodRows"] if x["muscle"] == "chest")
    assert chest["actual_exposures"] == 1


def test_rolling_windows_are_full_and_naive_timestamps_need_timezone():
    result = analyze_periods(TrainingHistory("S001", [plan()], []), DB, period="rolling_7_days", start="2026-01-01", end="2026-01-10", timezone="UTC")
    assert [(x["start"], x["end"]) for x in result["periods"]] == [("2026-01-01", "2026-01-07"), ("2026-01-02", "2026-01-08"), ("2026-01-03", "2026-01-09"), ("2026-01-04", "2026-01-10")]
    with raises_value_error("timezone is required"):
        analyze_periods(TrainingHistory("S001", [plan()], [workout("w", "2026-01-05") | {"startTime": "2026-01-05T00:00:00"}]), DB, start="2026-01-05", end="2026-01-11")


def test_timezone_local_week_boundary_is_deterministic():
    actual = workout("boundary", "2026-01-05", reference=False)
    actual["startTime"] = "2026-01-05T00:30:00Z"
    history = TrainingHistory("S001", [], [actual])
    for zone, expected in (("UTC", "2026-01-05"), ("America/New_York", "2025-12-29"), ("America/Chicago", "2025-12-29")):
        result = analyze_periods(history, DB, start="2025-12-29", end="2026-01-11", timezone=zone)
        assert next(x for x in result["sessionRows"] if x["session_id"] == "boundary")["period_start"] == expected


def test_target_transition_is_explicit_and_target_overlap_errors():
    targets = [{"targetId": "a", "periodDays": 7, "effectiveFrom": "2026-01-01", "effectiveTo": "2026-01-08", "muscles": {"chest": {"target": 4}}}, {"targetId": "b", "periodDays": 7, "effectiveFrom": "2026-01-08", "muscles": {"chest": {"target": 8}}}]
    result = analyze_periods(TrainingHistory("S001", [plan()], [], targets), DB, start="2026-01-05", end="2026-01-11", timezone="UTC")
    assert result["periods"][0]["targetProfilesUsed"] == ["a", "b"]
    assert next(x for x in result["musclePeriodRows"] if x["muscle"] == "chest")["target_state"] == "mixed_target"
    overlap = targets + [{"targetId": "c", "periodDays": 7, "effectiveFrom": "2026-01-05", "effectiveTo": "2026-01-07", "muscles": {"chest": {"target": 5}}}]
    with raises_value_error("overlapping target"):
        analyze_periods(TrainingHistory("S001", [plan()], [], overlap), DB, start="2026-01-05", end="2026-01-06", timezone="UTC")


def test_cohort_sorting_and_no_actual_missingness():
    result = analyze_cohort([TrainingHistory("S003", [plan()], []), TrainingHistory("S001", [plan()], [workout("w", "2026-01-05")]), TrainingHistory("S002", [plan()], [])], DB, start="2026-01-05", end="2026-01-11", timezone="UTC")
    assert result["subjects"] == ["S003", "S001", "S002"]
    assert [x["subject_id"] for x in result["musclePeriodRows"]] == sorted(x["subject_id"] for x in result["musclePeriodRows"])
    assert all(x["actual_exposures"] == 0 for x in result["musclePeriodRows"] if x["subject_id"] in {"S002", "S003"})
