import sys

from pathlib import Path
ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from src.analysis.coverage import analyze_plan
from src.analysis.targets import compare_to_targets, validate_target

DB = {"metadata": {"schemaVersion": "1.0.0", "setCredits":{"direct":1.0,"indirect":0.5,"stabilizer":0.0}}, "exercises": {
    "press": {"annotation": {"patterns": ["horizontal_push"], "direct": ["chest"], "indirect": ["triceps"], "stabilizers": ["shoulders"], "volumeEligible": True}},
    "row": {"annotation": {"patterns": ["horizontal_pull"], "direct": ["back"], "indirect": ["biceps"], "stabilizers": [], "volumeEligible": True}},
    "stretch": {"annotation": {"patterns": ["shoulder_mobility"], "direct": [], "indirect": [], "stabilizers": [], "volumeEligible": False}},
}}

PLAN = {"schemaVersion":"0.1.0","planId":"test-plan","revisionId":"r1","cycle":{"lengthDays":8},"sessions":[
    {"planSessionId":"s1","dayOffset":0,"exercises":[
        {"prescriptionId":"p1","exerciseId":"press","order":1,"sets":{"min":3,"target":4,"max":5},"reps":8},
        {"prescriptionId":"p2","exerciseId":"row","order":2,"sets":2,"reps":10},
        {"prescriptionId":"p3","exerciseName":"Custom","order":3,"sets":1,"reps":10},
        {"prescriptionId":"p4","exerciseId":"stretch","order":4,"sets":2,"reps":10}
    ]}
]}

def test_coverage_uses_target_sets_and_keeps_roles_separate():
    result = analyze_plan(PLAN, DB)
    native = result["nativeCycle"]
    assert native["directSets"] == {"back": 2.0, "chest": 4.0}
    assert native["indirectSets"] == {"biceps": 2.0, "triceps": 4.0}
    assert native["stabilizerParticipationSets"] == {"shoulders": 4.0}
    assert native["effectiveSets"] == {"back": 2.0, "biceps": 1.0, "chest": 4.0, "triceps": 2.0}
    assert native["movementPatternSets"] == {"horizontal_pull": 2.0, "horizontal_push": 4.0}
    assert result["normalized7Day"]["effectiveSets"]["chest"] == 3.5
    assert result["coverageCompleteness"]["plannedSets"] == 9.0
    assert result["coverageCompleteness"]["plannedSetRange"] == {"min": 8.0, "target": 9.0, "max": 10.0}
    assert result["coverageCompleteness"]["mappedFraction"] == round(8/9,6)
    assert result["nativeCycle"]["directSetRanges"]["chest"] == {"min": 3.0, "target": 4.0, "max": 5.0}

def test_target_gap_states_use_target_period():
    target={"schemaVersion":"0.1.0","targetId":"t","periodDays":8,"muscles":{"chest":{"min":3,"target":4,"max":5},"back":{"min":3},"biceps":{"max":0.5},"quadriceps":{"target":2}}}
    assert validate_target(target) == []
    result=compare_to_targets(PLAN,target,DB)
    assert result["muscles"]["chest"]["state"] == "at_target"
    assert result["muscles"]["back"]["state"] == "below_minimum"
    assert result["muscles"]["biceps"]["state"] == "above_maximum"
    assert result["muscles"]["quadriceps"]["state"] == "within_range_below_target"

def test_reversed_target_range_is_rejected():
    target={"schemaVersion":"0.1.0","targetId":"bad","periodDays":7,"muscles":{"chest":{"min":10,"target":8,"max":4}}}
    assert validate_target(target)
