"""Versioned, deterministic advisory progression policies."""
from __future__ import annotations
from copy import deepcopy
from typing import Any
from ._analysis.policies import COUNTED_SET_TYPES, planned_set_count, planned_set_range, representative_scalar
from ._analysis.units import UnitError, normalize_quantity

POLICIES={"hold-v1":{"policyId":"hold-v1","policyVersion":"1.0.0","description":"Always retain the supplied prescription.","parameters":{}},"double-progression-v1":{"policyId":"double-progression-v1","policyVersion":"1.0.0","description":"Increase a comparable load only after every required working set reaches the top of its rep range at acceptable specified effort.","parameters":{"loadIncrement":"required for load progression"}}}
DECISION_TYPES={"hold","increase_load","increase_reps","decrease_reps","increase_sets","decrease_sets","insufficient_data"}
REASONS={"POLICY_HOLD","REP_TARGET_ACHIEVED","REP_TARGET_NOT_ACHIEVED","SET_TARGET_NOT_COMPLETED","EFFORT_WITHIN_TARGET","EFFORT_TOO_HIGH","EFFORT_TOO_LOW","INSUFFICIENT_EFFORT_DATA","INSUFFICIENT_LOAD_DATA","INCOMPATIBLE_LOAD_UNIT","INCOMPLETE_WORKOUT","NO_MATCHED_ACTUAL","NO_ACTIVE_PLAN","NO_RECENT_PERFORMANCE"}

def _doc(x): return x.document if hasattr(x,"document") else x
def _result(policy, typ, prescription, state, reasons, *, after=None, evidence=None):
    before={k:deepcopy(prescription.get(k)) for k in ("load","reps","sets") if k in prescription}; after=after or deepcopy(before)
    return {"schemaVersion":"0.1.0","decisionType":typ,"policyId":policy["policyId"],"policyVersion":policy["policyVersion"],"planId":state.get("planId"),"revisionId":state.get("revisionId"),"prescriptionId":prescription.get("prescriptionId"),"exerciseId":prescription.get("exerciseId"),"before":before,"after":after,"reasonCodes":sorted(set(reasons)),"evidence":evidence or {},"provenance":state.get("provenance",{})}

def _validate(policy_id, parameters):
    if policy_id not in POLICIES: raise ValueError(f"unknown progression policy: {policy_id}")
    p=parameters or {}; inc=p.get("loadIncrement")
    if inc is not None and (not isinstance(inc,dict) or float(inc.get("value",0))<=0 or not inc.get("unit")): raise ValueError("loadIncrement requires a positive value and unit")

def apply_progression_policy(policy, prescription, exercise_state, *, db=None, parameters=None):
    pid=policy if isinstance(policy,str) else (policy or {}).get("policyId")
    params=parameters or (policy.get("parameters",{}) if isinstance(policy,dict) else {}) or {}; _validate(pid,params); p=POLICIES[pid]
    state=exercise_state or {}; context=state.get("planContext",{}) if isinstance(state,dict) else {}
    if pid=="hold-v1": return _result(p,"hold",prescription,context,["POLICY_HOLD"])
    actual=state.get("lastActual")
    if not actual: return _result(p,"insufficient_data",prescription,context,["NO_RECENT_PERFORMANCE","NO_MATCHED_ACTUAL"])
    planned_items=[x for x in prescription.get("plannedSets",[]) if x.get("setType") in COUNTED_SET_TYPES] if prescription.get("plannedSets") is not None else []
    required=len(planned_items) if planned_items else int(planned_set_count(prescription))
    sets=[x for x in actual.get("sets",[]) if x.get("completed") is True and (x.get("setType") is None or x.get("setType") in COUNTED_SET_TYPES)]
    if len(sets)<required: return _result(p,"hold",prescription,context,["SET_TARGET_NOT_COMPLETED","INCOMPLETE_WORKOUT"],evidence={"plannedSetCount":required,"actualSetCount":len(sets)})
    rep=prescription.get("reps"); top=(rep or {}).get("max") if isinstance(rep,dict) else rep
    if top is None and isinstance(rep,dict): top=(rep.get("target") if rep.get("target") is not None else rep.get("min"))
    comparisons=[]; by_id={x.get("setPrescriptionId"):x for x in planned_items}
    if planned_items and any(s.get("setPrescriptionId") is not None for s in sets):
        if any(s.get("setPrescriptionId") not in by_id for s in sets): return _result(p,"insufficient_data",prescription,context,["NO_MATCHED_ACTUAL"],evidence={"sets":sets})
        ordered=[by_id[s.get("setPrescriptionId")] for s in sets if s.get("setPrescriptionId") is not None]
    else: ordered=planned_items or [prescription] * required
    for i,s in enumerate(sets[:required]):
        expected=ordered[i] if i < len(ordered) else prescription; expected_rep=expected.get("reps",rep)
        expected_top=(expected_rep or {}).get("max") if isinstance(expected_rep,dict) else expected_rep
        if expected_top is None and isinstance(expected_rep,dict): expected_top=expected_rep.get("target",expected_rep.get("min"))
        if s.get("reps") is None or expected_top is None: return _result(p,"insufficient_data",prescription,context,["REP_TARGET_NOT_ACHIEVED"],evidence={"sets":sets})
        comparisons.append({"setId":s.get("setPrescriptionId") or s.get("setNumber"),"plannedReps":expected_rep,"actualReps":s.get("reps")})
    def rep_top(v): return v.get("max",v.get("target",v.get("min"))) if isinstance(v,dict) else v
    if any(float(x["actualReps"]) < float(rep_top(x["plannedReps"])) for x in comparisons): return _result(p,"hold",prescription,context,["REP_TARGET_NOT_ACHIEVED"],evidence={"sets":comparisons})
    reasons=["REP_TARGET_ACHIEVED"]; effort=(prescription.get("effort") or {}); effort_key=next((x for x in ("rir","rpe") if x in effort),None)
    if effort_key:
        actual_eff=[s.get(effort_key) for s in sets[:required]]
        if any(x is None for x in actual_eff): return _result(p,"insufficient_data",prescription,context,["INSUFFICIENT_EFFORT_DATA"],evidence={"sets":comparisons,"effortType":effort_key})
        bounds=effort[effort_key]; lo=bounds.get("min",bounds.get("target")); hi=bounds.get("max",bounds.get("target"));
        if any(lo is not None and float(x)<float(lo) or hi is not None and float(x)>float(hi) for x in actual_eff): return _result(p,"hold",prescription,context,["EFFORT_TOO_HIGH" if effort_key=="rpe" else "EFFORT_TOO_LOW"],evidence={"sets":comparisons,"actualEffort":actual_eff})
        reasons.append("EFFORT_WITHIN_TARGET")
    load=prescription.get("load"); inc=params.get("loadIncrement")
    if not load or load.get("value",load.get("target")) is None: return _result(p,"insufficient_data",prescription,context,["INSUFFICIENT_LOAD_DATA"],evidence={"sets":comparisons})
    if not inc: return _result(p,"insufficient_data",prescription,context,["INSUFFICIENT_LOAD_DATA"],evidence={"sets":comparisons})
    unit=str(load.get("unit","")).lower(); incunit=str(inc.get("unit","")).lower()
    try: current=normalize_quantity({"value":load.get("value",load.get("target")),"unit":unit},"kg"); delta=normalize_quantity({"value":inc["value"],"unit":incunit},"kg")
    except (UnitError,ValueError,TypeError): return _result(p,"insufficient_data",prescription,context,["INCOMPATIBLE_LOAD_UNIT"],evidence={"sets":comparisons})
    if unit not in {"kg","lb","g"}: return _result(p,"insufficient_data",prescription,context,["INCOMPATIBLE_LOAD_UNIT"],evidence={"sets":comparisons})
    new=round(normalize_quantity({"value":current+delta,"unit":"kg"},unit),6); after=deepcopy({k:prescription[k] for k in ("load","reps","sets") if k in prescription}); after["load"]={**load,"value":new}; after["load"].pop("target",None)
    return _result(p,"increase_load",prescription,context,reasons,after=after,evidence={"sets":comparisons,"previousLoad":load,"newLoad":after["load"]})

def suggest_progression(plan, training_state, *, policy="double-progression-v1", parameters=None):
    plan=_doc(plan); state=_doc(training_state); active=state.get("activePlan",{})
    _validate(policy if isinstance(policy,str) else (policy or {}).get("policyId"), parameters)
    if active.get("revisionId") and active.get("revisionId")!=plan.get("revisionId"): raise ValueError("plan is not the active TrainingState revision")
    out=[]
    if not active.get("planId") or not active.get("revisionId"):
        selected = POLICIES[policy] if isinstance(policy,str) and policy in POLICIES else POLICIES["hold-v1"]
        for session in plan.get("sessions",[]):
            for rx in session.get("exercises",[]): out.append(_result(selected,"insufficient_data",rx,{"planId":plan.get("planId"),"revisionId":plan.get("revisionId"),"provenance":state.get("provenance",{})},["NO_ACTIVE_PLAN"]))
        return out
    for session in plan.get("sessions",[]):
        for rx in session.get("exercises",[]):
            es=deepcopy(state.get("exerciseState",{}).get(rx.get("exerciseId"),{})); es["planContext"]={"planId":plan.get("planId"),"revisionId":plan.get("revisionId"),"provenance":state.get("provenance",{})}; out.append(apply_progression_policy(policy,rx,es,parameters=parameters))
    return out

def suggest_progression_for_plan(active_plan, training_state, *, policy_map=None, parameters=None):
    plan=_doc(active_plan); return [suggest_progression(plan,training_state,policy=policy_map.get(rx.get("prescriptionId"),"hold-v1") if policy_map else "hold-v1",parameters=parameters)[i] for i,rx in enumerate([rx for s in plan.get("sessions",[]) for rx in s.get("exercises",[])])]

__all__=["apply_progression_policy","suggest_progression","suggest_progression_for_plan","POLICIES","REASONS"]
