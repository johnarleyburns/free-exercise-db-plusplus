from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from fedbpp import Database, TrainingHistory, derive_training_state, suggest_progression, suggest_progression_for_plan

DB=Database({"metadata":{"schemaVersion":"db","converterVersion":"c","upstream":{"sha256":"a"*64},"setCredits":{"direct":1,"indirect":.5,"stabilizer":0}},"exercises":{"e":{"annotation":{"direct":["chest"],"indirect":[],"stabilizers":[],"patterns":[],"volumeEligible":True}}}})
PLAN={"schemaVersion":"0.2.0","planId":"p","revisionId":"r","cycle":{"lengthDays":7},"sessions":[{"planSessionId":"s","dayOffset":0,"exercises":[{"prescriptionId":"rx","exerciseId":"e","sets":3,"reps":{"min":8,"max":10},"load":{"value":100,"unit":"kg"},"effort":{"rir":{"target":2}}}]}]}

def workout(reps=(10,10,10), *, rir=(2,2,2)):
    return {"schemaVersion":"0.3.0","sessionId":"w","startTime":"2026-08-24T12:00:00Z","planReference":{"planId":"p","revisionId":"r","planSessionId":"s"},"exercises":[{"exerciseId":"e","exercisePrescriptionId":"rx","sets":[{"setNumber":i+1,"setType":"working","completed":True,"reps":reps[i],"load":{"value":100,"unit":"kg"},"rir":rir[i]} for i in range(3)]}]}

def state(w):
    return derive_training_state(TrainingHistory("s",[PLAN],[w],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window="last_28_days",timezone="UTC")

def test_state_and_double_progression_success():
    s=state(workout()); assert s["activePlan"]["revisionId"]=="r"; assert s["exerciseState"]["e"]["recentReps"]==[10,10,10]; assert s["provenance"]["setCredits"]["indirect"]==.5
    d=suggest_progression(PLAN,s,parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})[0]; assert d["decisionType"]=="increase_load"; assert d["after"]["load"]["value"]==102.5; assert "REP_TARGET_ACHIEVED" in d["reasonCodes"]

def test_partial_effort_and_missing_effort_are_explicit():
    assert suggest_progression(PLAN,state(workout((10,10,8))),parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})[0]["decisionType"]=="hold"
    missing=workout(); del missing["exercises"][0]["sets"][1]["rir"]; assert suggest_progression(PLAN,state(missing),parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})[0]["decisionType"]=="insufficient_data"

def test_window_excludes_future_and_no_plan_is_not_recent_performance():
    future=workout(); future["startTime"]="2026-09-01T12:00:00Z"; s=state(future); assert s["exerciseState"]["e"]["recentSessionCount"]==0
    no=derive_training_state(TrainingHistory("s",[],[]),DB,as_of="2026-08-25T00:00:00Z",window="last_7_days",timezone="UTC"); assert no["activePlan"]["planId"] is None

def test_hold_policy_and_bad_increment():
    d=suggest_progression(PLAN,state(workout()),policy="hold-v1")[0]; assert d["decisionType"]=="hold" and d["reasonCodes"]==["POLICY_HOLD"]
    try: suggest_progression(PLAN,state(workout()),parameters={"loadIncrement":{"value":0,"unit":"kg"}})
    except ValueError: pass
    else: assert False

def effort_decision(metric, value, prescribed):
    plan=deepcopy(PLAN); plan["sessions"][0]["exercises"][0]["effort"]={metric:prescribed}
    actual=workout(rir=(2,2,2));
    for item in actual["exercises"][0]["sets"]:
        item.pop("rir", None); item[metric]=value
    s=derive_training_state(TrainingHistory("s",[plan],[actual],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window="last_28_days",timezone="UTC")
    return suggest_progression(plan,s,parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})[0]

def test_all_effort_direction_reason_codes():
    assert "EFFORT_TOO_LOW" in effort_decision("rpe", 6, {"min":7,"max":8})["reasonCodes"]
    assert "EFFORT_TOO_HIGH" in effort_decision("rpe", 9, {"min":7,"max":8})["reasonCodes"]
    assert "EFFORT_TOO_HIGH" in effort_decision("rir", 1, {"min":2,"max":3})["reasonCodes"]
    assert "EFFORT_TOO_LOW" in effort_decision("rir", 4, {"min":2,"max":3})["reasonCodes"]
    assert "EFFORT_WITHIN_TARGET" in effort_decision("rpe", 7.5, {"min":7,"max":8})["reasonCodes"]

def test_effort_schema_accepts_corrected_decisions_and_missing_is_explicit():
    missing=workout(); missing["exercises"][0]["sets"][1].pop("rir")
    decision=suggest_progression(PLAN,state(missing),parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})[0]
    assert decision["decisionType"]=="insufficient_data" and "INSUFFICIENT_EFFORT_DATA" in decision["reasonCodes"]
    schema=json.loads(Path("coach-decision.schema.json").read_text())
    Draft202012Validator(schema).validate(effort_decision("rpe", 6, {"min":7,"max":8}))
    Draft202012Validator(schema).validate(effort_decision("rpe", 9, {"min":7,"max":8}))
    Draft202012Validator(schema).validate(effort_decision("rir", 1, {"min":2,"max":3}))
    Draft202012Validator(schema).validate(effort_decision("rir", 4, {"min":2,"max":3}))

def test_adherence_counts_per_prescription_and_provenance_window():
    plan=deepcopy(PLAN); plan["sessions"][0]["exercises"][0]["prescriptionId"]="rx-a"
    second=deepcopy(plan["sessions"][0]); second["planSessionId"]="s2"; second["dayOffset"]=1; second["exercises"][0]["prescriptionId"]="rx-b"
    plan["sessions"].append(second)
    actual=workout(); actual["startTime"]="2026-08-22T12:00:00Z"; actual["exercises"][0]["exercisePrescriptionId"]="rx-a"
    actual["planReference"]["planSessionId"]="s"
    future=deepcopy(actual); future["sessionId"]="future"; future["startTime"]="2026-09-01T12:00:00Z"; future["planReference"]["planSessionId"]="s2"; future["exercises"][0]["exercisePrescriptionId"]="rx-b"
    h=TrainingHistory("s",[plan],[actual,future],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}])
    s=derive_training_state(h,DB,as_of="2026-08-25T12:00:00Z",window={"start":"2026-08-22","end":"2026-08-25"},timezone="UTC")
    assert set(s["exerciseState"]["e"]["prescriptionAdherenceByPrescriptionId"])=={"rx-a","rx-b"}
    assert s["exerciseState"]["e"]["prescriptionAdherenceByPrescriptionId"]["rx-a"]["matchedOccurrences"]==1
    assert s["exerciseState"]["e"]["prescriptionAdherenceByPrescriptionId"]["rx-b"]["missingOccurrences"]==1
    assert s["provenance"]["historyWindow"]=={"type":{"start":"2026-08-22","end":"2026-08-25"},"start":"2026-08-22","end":"2026-08-25"}
    assert all(p["timestamp"] <= "2026-08-25T12:00:00Z" for p in s["exerciseState"]["e"]["recentPerformances"])

def test_performance_fields_are_latest_and_deterministically_recent():
    older=workout(); older["sessionId"]="a"; older["startTime"]="2026-08-10T12:00:00Z"
    newer=workout((9,9,9)); newer["sessionId"]="b"; newer["startTime"]="2026-08-20T12:00:00Z"
    s=derive_training_state(TrainingHistory("s",[PLAN],[newer,older],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window="last_28_days",timezone="UTC")
    es=s["exerciseState"]["e"]
    assert es["latestPerformance"]["sessionId"]=="b" and [x["sessionId"] for x in es["recentPerformances"]]==["a","b"]
    assert es["recentReps"]==[9,9,9]

def test_repeated_skip_and_substitution_counts_are_quantitative():
    plan=deepcopy(PLAN); plan["sessions"][0]["exercises"][0]["prescriptionId"]="rx-bench"
    skipped=derive_training_state(TrainingHistory("s",[plan],[],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window={"start":"2026-08-08","end":"2026-08-25"},timezone="UTC")
    assert skipped["adherenceState"]["skippedPrescriptionCounts"]=={"rx-bench":3}
    substitutions=[]
    for day, sid in (("2026-08-08","a"),("2026-08-15","b")):
        w=workout(); w["sessionId"]=sid; w["startTime"]=day+"T12:00:00Z"; w["exercises"][0]["exerciseId"]="sub"; w["exercises"][0]["exercisePrescriptionId"]="rx-bench"; w["exercises"][0]["substitution"]={"plannedPrescriptionId":"rx-bench","reason":"equipment"}; substitutions.append(w)
    substituted=derive_training_state(TrainingHistory("s",[plan],substitutions,plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window={"start":"2026-08-08","end":"2026-08-25"},timezone="UTC")
    assert substituted["adherenceState"]["substitutionCountsByPrescription"]=={"rx-bench":2}

def test_policy_map_evaluates_each_prescription_in_plan_order():
    plan=deepcopy(PLAN); plan["sessions"][0]["exercises"]=[{"prescriptionId":"rx-a","exerciseId":"e","sets":3,"reps":{"min":8,"max":10},"load":{"value":100,"unit":"kg"}}, {"prescriptionId":"rx-b","exerciseId":"e","sets":3,"reps":{"min":8,"max":10},"load":{"value":100,"unit":"kg"}}, {"prescriptionId":"rx-c","exerciseId":"e","sets":3,"reps":{"min":8,"max":10},"load":{"value":100,"unit":"kg"}}]
    actual=workout(); actual["exercises"]= [{"exerciseId":"e","exercisePrescriptionId":rx,"sets":[{"setNumber":i,"setType":"working","completed":True,"reps":10,"load":{"value":100,"unit":"kg"}} for i in range(1,4)]} for rx in ("rx-a","rx-b","rx-c")]
    s=derive_training_state(TrainingHistory("s",[plan],[actual],plan_activations=[{"planId":"p","revisionId":"r","effectiveFrom":"2026-08-01T00:00:00Z"}]),DB,as_of="2026-08-25T12:00:00Z",window="last_28_days",timezone="UTC")
    out=suggest_progression_for_plan(plan,s,policy_map={"rx-a":"double-progression-v1","rx-b":"hold-v1","rx-c":"double-progression-v1"},parameters={"loadIncrement":{"value":2.5,"unit":"kg"}})
    assert [x["prescriptionId"] for x in out]==["rx-a","rx-b","rx-c"]
    assert [x["policyId"] for x in out]==["double-progression-v1","hold-v1","double-progression-v1"]
