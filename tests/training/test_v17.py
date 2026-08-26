from fedbpp import Database, TrainingHistory, derive_training_state, suggest_progression

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
