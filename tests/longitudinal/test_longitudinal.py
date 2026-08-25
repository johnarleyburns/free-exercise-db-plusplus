from fedbpp import Database, TrainingHistory, analyze_cohort, analyze_periods, export_muscle_period_csv


DB = {"metadata": {"schemaVersion": "0.3.0", "converterVersion": "0.8.0", "setCredits": {"direct": 1.0, "indirect": 0.5, "stabilizer": 0.0}}, "exercises": {"press": {"exerciseId": "press", "annotation": {"direct": ["chest"], "indirect": ["triceps"], "stabilizers": [], "patterns": ["horizontal_push"], "volumeEligible": True}}}}
PLAN = {"schemaVersion": "0.2.0", "planId": "p", "revisionId": "r1", "name": "P", "cycle": {"lengthDays": 7}, "sessions": [{"planSessionId": "upper", "dayOffset": 0, "exercises": [{"prescriptionId": "rx", "exerciseId": "press", "order": 1, "sets": {"min": 2}}]}]}


def workout(session_id, stamp, count=2):
    return {"schemaVersion": "0.3.0", "sessionId": session_id, "startTime": stamp, "planReference": {"planId": "p", "revisionId": "r1", "planSessionId": "upper"}, "exercises": [{"exerciseId": "press", "exercisePrescriptionId": "rx", "sets": [{"setNumber": n, "setType": "working", "completed": True} for n in range(1, count + 1)]}]}


def test_period_analysis_distinguishes_missed_and_preserves_partial_ranges():
    history = TrainingHistory("S001", [PLAN], [workout("a", "2026-01-05T12:00:00-05:00")], [{"schemaVersion": "0.1.0", "targetId": "t", "periodDays": 7, "muscles": {"chest": {"min": 2, "max": 4}}}])
    result = analyze_periods(history, Database(DB), start="2026-01-05", end="2026-01-11", timezone="America/New_York")
    assert result["periods"][0]["scheduledPlannedSessions"] == 1
    assert result["periods"][0]["completedPlannedSessions"] == 1
    chest = next(row for row in result["musclePeriodRows"] if row["muscle"] == "chest")
    assert chest["planned_effective_target"] is None
    assert chest["planned_effective_min"] == 2
    assert chest["target_state"] == "within_range"
    assert "analysisVersion" in result["provenance"]


def test_csv_and_cohort_are_deterministic():
    db = Database(DB)
    first = analyze_periods(TrainingHistory("S002", [PLAN], [workout("b", "2026-01-05T12:00:00Z", 1)]), db, start="2026-01-05", end="2026-01-11", timezone="UTC")
    cohort = analyze_cohort([TrainingHistory("S002", [PLAN], [workout("b", "2026-01-05T12:00:00Z", 1)]), TrainingHistory("S001", [PLAN], [])], db, start="2026-01-05", end="2026-01-11", timezone="UTC")
    assert [row["subject_id"] for row in cohort["musclePeriodRows"]] == sorted(row["subject_id"] for row in cohort["musclePeriodRows"])
    csv = export_muscle_period_csv(first)
    assert csv.startswith("subject_id,period_type,period_start")
    assert "S002" in csv
