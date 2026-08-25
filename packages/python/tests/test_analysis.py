from fedbpp import Database, Plan
from fedbpp.analysis import analyze


def test_public_analysis_api():
    db = Database({"metadata": {"schemaVersion": "1.0.0"}, "exercises": {}})
    plan = Plan.from_dict({
        "schemaVersion": "0.1.0", "planId": "p", "revisionId": "r", "name": "P",
        "cycle": {"lengthDays": 7}, "sessions": [{
            "planSessionId": "s", "dayOffset": 0,
            "exercises": [{"prescriptionId": "x", "exerciseName": "Custom", "order": 1, "sets": 1, "reps": 5}],
        }],
    })
    assert analyze(plan, db)["plan"]["planId"] == "p"


def test_required_public_analysis_names():
    from fedbpp import VolumeTarget, analyze_plan, compare_plans, compare_to_targets, compare_plan_actual
    target = VolumeTarget.from_dict({"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{"chest":{"min":1}}}, validate=False)
    assert target.document["targetId"] == "t"
    assert all(callable(value) for value in (analyze_plan, compare_plans, compare_to_targets, compare_plan_actual))
