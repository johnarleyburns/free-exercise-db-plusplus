import sys
from pathlib import Path
ROOT=Path(__file__).parents[2]; sys.path.insert(0,str(ROOT))
from src.analysis import analyze_plan_actual

DB={"metadata":{"schemaVersion":"1.0.0"},"exercises":{
 "press":{"annotation":{"patterns":["horizontal_push"],"direct":["chest"],"indirect":["triceps"],"stabilizers":[],"volumeEligible":True}},
 "row":{"annotation":{"patterns":["horizontal_pull"],"direct":["back"],"indirect":["biceps"],"stabilizers":[],"volumeEligible":True}},
 "curl":{"annotation":{"patterns":["elbow_flexion"],"direct":["biceps"],"indirect":[],"stabilizers":[],"volumeEligible":True}},
}}
PLAN={"schemaVersion":"0.1.0","planId":"p","revisionId":"r1","cycle":{"lengthDays":7},"sessions":[{"planSessionId":"upper","dayOffset":0,"exercises":[
 {"prescriptionId":"press-1","exerciseId":"press","order":1,"sets":3,"reps":8},
 {"prescriptionId":"row-1","exerciseId":"row","order":2,"sets":2,"reps":{"min":8,"max":12}},
 {"prescriptionId":"curl-1","exerciseId":"curl","order":3,"sets":2,"reps":10}
]}]}
WORKOUT={"schemaVersion":"0.3.0","sessionId":"actual-1","startTime":"2026-01-01T00:00:00Z","planReference":{"planId":"p","revisionId":"r1","planSessionId":"upper"},"exercises":[
 {"exerciseId":"press","exercisePrescriptionId":"press-1","order":1,"sets":[{"setNumber":1,"setType":"working","reps":8,"completed":True},{"setNumber":2,"setType":"working","reps":7,"completed":True},{"setNumber":3,"setType":"working","reps":8,"completed":False}]},
 {"exerciseId":"row","exercisePrescriptionId":"row-1","order":2,"sets":[{"setNumber":1,"setType":"working","reps":10,"completed":True}],"substitution":{"reason":"machine unavailable","plannedPrescriptionId":"row-1"}},
 {"exerciseId":"unknown","order":3,"sets":[{"setNumber":1,"setType":"working","reps":10,"completed":True}]},
 {"exerciseId":"press","order":4,"sets":[{"setNumber":1,"setType":"working","reps":8,"completed":True}]}
]}

def test_explicit_matching_statuses_and_missing_prescription():
 result=analyze_plan_actual(PLAN,WORKOUT,DB); matching=result["matching"]
 assert matching["sessionStatus"]=="matched"
 assert matching["exerciseStatuses"]=={"matched":1,"substitution":1,"unplanned_addition":2,"missing_prescription":1}
 assert matching["missingPrescriptions"]==["curl-1"]
 assert [row["status"] for row in matching["exercises"]]==["matched","substitution","unplanned_addition","unplanned_addition"]

def test_adherence_calculates_sets_reps_muscles_and_patterns():
 result=analyze_plan_actual(PLAN,WORKOUT,DB); rows=result["matching"]["exercises"]
 assert rows[0]["actualCompletedSets"]==2 and rows[0]["repsAdherentSets"]==1
 assert result["adherence"]["muscles"]["chest"]=={"planned":3.0,"actual":2.0,"delta":-1.0,"fraction":round(2/3,6)}
 assert result["adherence"]["muscles"]["back"]=={"planned":2.0,"actual":1.0,"delta":-1.0,"fraction":0.5}
 assert result["adherence"]["movementPatterns"]["horizontal_push"]["actual"]==2.0

def test_missing_plan_reference_is_unable_without_fuzzy_matching():
 workout={**WORKOUT}; workout.pop("planReference")
 result=analyze_plan_actual(PLAN,workout,DB)
 assert result["matching"]["sessionStatus"]=="unable_to_match"
