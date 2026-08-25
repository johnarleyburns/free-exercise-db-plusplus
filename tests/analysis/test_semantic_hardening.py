"""Hand-calculated semantic hardening regression anchor."""
import sys
from pathlib import Path
ROOT=Path(__file__).parents[2]; sys.path.insert(0,str(ROOT))
from src.analysis.coverage import analyze_plan
from src.analysis.plan_actual import analyze_plan_actual
from src.analysis.targets import compare_to_targets, validate_target
from src.analysis.policies import completed_exercise_sets
from src.plan.validate_plan import semantic_errors

DB={"metadata":{"schemaVersion":"0.3.0","converterVersion":"test","upstream":{"sha256":"abc"},"setCredits":{"direct":2,"indirect":.25,"stabilizer":.1}},"exercises":{
 "bench":{"annotation":{"patterns":["push"],"direct":["chest"],"indirect":["triceps"],"stabilizers":["shoulders"],"volumeEligible":True}},
 "row":{"annotation":{"patterns":["pull"],"direct":["back"],"indirect":["biceps"],"stabilizers":[],"volumeEligible":True}},
 "mobility":{"annotation":{"patterns":["mobility"],"direct":["shoulders"],"indirect":[],"stabilizers":[],"volumeEligible":False}},
 "squat":{"annotation":{"patterns":["squat"],"direct":["quadriceps"],"indirect":[],"stabilizers":[],"volumeEligible":True}},
 "raise":{"annotation":{"patterns":["abduction"],"direct":["shoulders"],"indirect":[],"stabilizers":[],"volumeEligible":True}}}}
PLAN={"schemaVersion":"0.2.0","planId":"gold","revisionId":"r1","cycle":{"lengthDays":8},"sessions":[{"planSessionId":"s1","dayOffset":0,"exercises":[
 {"prescriptionId":"bench-rx","exerciseId":"bench","order":1,"sets":{"min":3,"target":4,"max":5},"reps":8,"load":{"value":100,"unit":"kg"},"effort":{"rpe":{"min":7,"target":8,"max":9}}},
 {"prescriptionId":"row-rx","exerciseId":"row","order":2,"plannedSets":[{"setPrescriptionId":"row-top","setType":"working","reps":6,"load":{"value":100,"unit":"kg"},"effort":{"rir":2}},{"setPrescriptionId":"row-back","setType":"backoff","reps":{"min":8,"target":10,"max":12},"load":{"value":80,"unit":"kg"}}]},
 {"prescriptionId":"mob-rx","exerciseId":"mobility","order":3,"sets":2,"reps":10},
 {"prescriptionId":"squat-rx","exerciseId":"squat","order":4,"sets":2,"reps":5}]}]}
ACTUAL={"schemaVersion":"0.3.0","sessionId":"actual","planReference":{"planId":"gold","revisionId":"r1","planSessionId":"s1"},"exercises":[
 {"exerciseId":"bench","exercisePrescriptionId":"bench-rx","sets":[{"setNumber":1,"setType":"warmup","reps":8,"completed":True},{"setNumber":2,"setType":"working","reps":8,"load":{"value":220.462262,"unit":"lb"},"rpe":8,"completed":True},{"setNumber":3,"setType":"working","reps":8,"load":{"value":100,"unit":"kg"},"rpe":8,"completed":True},{"setNumber":4,"setType":"working","reps":8,"completed":False}]},
 {"exerciseId":"row","exercisePrescriptionId":"row-rx","sets":[{"setNumber":1,"setPrescriptionId":"row-top","setType":"working","reps":6,"load":{"value":100,"unit":"kg"},"rir":2,"completed":True},{"setNumber":2,"setPrescriptionId":"bad-id","setType":"backoff","reps":10,"load":{"value":80,"unit":"kg"},"completed":True}]},
 {"exerciseId":"raise","sets":[{"setNumber":1,"setType":"working","reps":12,"completed":True},{"setNumber":2,"setType":"drop","reps":12,"completed":True,"segments":[{"reps":5}]}]}]}

def test_authoritative_credits_ranges_ineligibility_frequency_and_provenance():
 a=analyze_plan(PLAN,DB); n=a["nativeCycle"]
 assert n["directSetRanges"]["chest"]=={"min":3.0,"target":4.0,"max":5.0}
 assert n["effectiveSetRanges"]["chest"]=={"min":6.0,"target":8.0,"max":10.0}
 assert n["effectiveSetRanges"]["triceps"]=={"min":.75,"target":1.0,"max":1.25}
 assert "mobility" not in n["movementPatternSets"] and a["coverageCompleteness"]["ineligibleSets"]==2
 assert a["analysisPolicy"]=="dbpp-default-volume-v1" and a["analysisMetadata"]["setCredits"]["direct"]==2
 assert a["exposureFrequency"]["muscles"]["chest"]["exposuresPerNativeCycle"]==1

def test_count_policy_and_unplanned_actual_coverage_and_matching():
 assert len(completed_exercise_sets(ACTUAL["exercises"][0]))==2
 r=analyze_plan_actual(PLAN,ACTUAL,DB)
 assert r["matching"]["exercises"][0]["setRangeAdherence"]=={"plannedRange":{"min":3.0,"target":4.0,"max":5.0},"actual":2.0,"meetsMinimum":False,"meetsTarget":False,"withinMaximum":True,"differenceFromTarget":-2.0}
 bad=next(x for x in r["matching"]["sets"] if x.get("setPrescriptionId")=="bad-id")
 assert bad["status"]=="unable_to_match"
 assert any(x.get("setPrescriptionId")=="row-back" and x["status"]=="missing_prescription" for x in r["matching"]["sets"])
 assert r["unplannedActualCoverage"]["directSets"]["shoulders"]==2
 assert r["totalActualCoverage"]["directSets"]["shoulders"]==2
 assert r["adherence"]["muscles"]["chest"]["direct"]["actual"]==2
 bench_sets=[x for x in r["matching"]["sets"] if x.get("prescriptionId")=="bench-rx" and x.get("counted")]
 assert all(x["load"]["comparable"] and x["load"]["withinRange"] for x in bench_sets)
 assert all(x["rpe"]["comparable"] and x["rpe"]["withinRange"] for x in bench_sets)
 top=next(x for x in r["matching"]["sets"] if x.get("setPrescriptionId")=="row-top")
 assert top["rir"]["comparable"] and top["rir"]["withinRange"]
 bench=next(x for x in r["matching"]["exercises"] if x.get("prescriptionId")=="bench-rx")
 assert bench["volumeLoad"]["comparable"] and round(bench["volumeLoad"]["planned"],6)==3200
 assert round(bench["volumeLoad"]["actual"],3)==1600
 assert r["analysisMetadata"]["workoutSchemaVersion"]=="0.3.0"

def test_target_states_and_db_validation():
 target={"schemaVersion":"0.1.0","targetId":"t","periodDays":8,"muscles":{"chest":{"min":6,"target":8,"max":10},"back":{"min":5},"shoulders":{"max":3}}}
 assert validate_target(target,db=DB)==[]
 result=compare_to_targets(PLAN,target,DB); assert result["muscles"]["chest"]["state"]=="at_target"; assert result["muscles"]["back"]["state"]=="below_minimum"
 bad={**target,"muscles":{"unknown":{"min":1}}}; assert validate_target(bad,db=DB)==["muscles.unknown: unknown DB++ muscle ID"]

def test_plan_versions_and_xor():
 old={**PLAN,"schemaVersion":"0.1.0","phases":[{"phaseId":"p","durationCycles":1}]}; assert any("requires PLAN" in e for e in semantic_errors(old))
 mixed={**PLAN,"sessions":[{"planSessionId":"x","dayOffset":0,"exercises":[{"prescriptionId":"x","exerciseId":"bench","order":1,"sets":2,"reps":8,"plannedSets":[{"setPrescriptionId":"x1","setType":"working","reps":8}]}]}]}; assert any("mutually exclusive" in e for e in semantic_errors(mixed))

def test_phase_specific_cycle_and_duration_weighting():
 plan={"schemaVersion":"0.2.0","planId":"p","revisionId":"r","cycle":{"lengthDays":7},"phases":[{"phaseId":"a","durationCycles":3,"cycle":{"lengthDays":8}},{"phaseId":"b","durationCycles":1,"cycle":{"lengthDays":6}}],"sessions":[{"planSessionId":"a1","phaseId":"a","dayOffset":0,"exercises":[{"prescriptionId":"a","exerciseId":"bench","order":1,"sets":6.857142857,"reps":8}]},{"planSessionId":"b1","phaseId":"b","dayOffset":0,"exercises":[{"prescriptionId":"b","exerciseId":"bench","order":1,"sets":1.714285714,"reps":8}]}]}
 a=analyze_plan(plan,DB); phases=a["periodization"]["phases"]; assert [p["nativeCycle"]["periodDays"] for p in phases]==[8,6]
 assert round(a["periodization"]["normalizedEffectiveSetRangesDurationWeightedAverage"]["chest"]["target"],6)==10
