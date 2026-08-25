"""Explicit-reference-first PLAN-vs-ACTUAL matching and adherence."""
from __future__ import annotations
from collections import defaultdict
from typing import Any
from .coverage import analyze_plan, _annotation, _exercise, _metadata
from .matching import match_plan_actual
from .policies import ANALYSIS_POLICY, ANALYSIS_VERSION, COUNTED_SET_TYPES, RANGE_POLICY, UNIT_POLICY, completed_exercise_sets, normalize_range, planned_set_range, set_credits, set_is_counted
from .units import UnitError, normalize_quantity

def _adherence(planned, actual):
    p=float(planned); a=float(actual); return {"planned":round(p,6),"actual":round(a,6),"delta":round(a-p,6),"fraction":round(a/p,6) if p else None}

def _metric_coverage(exercises, db):
    direct,indirect,stabilizers,patterns=(defaultdict(float) for _ in range(4)); counted=mapped=unmapped=ineligible=0
    credits=set_credits(db)
    for actual in exercises:
      sets=completed_exercise_sets(actual); count=len(sets); counted += count
      eid=actual.get("exerciseId")
      try: ann=_annotation(_exercise(db,eid)) if eid else None
      except (KeyError,TypeError): ann=None
      if ann is None: unmapped += count; continue
      mapped += count
      if not ann.get("volumeEligible",False): ineligible += count; continue
      for m in ann.get("direct",[]): direct[m]+=count
      for m in ann.get("indirect",[]): indirect[m]+=count
      for m in ann.get("stabilizers",[]): stabilizers[m]+=count
      for p in ann.get("patterns",[]): patterns[p]+=count
    effective={m:direct[m]*credits["direct"]+indirect[m]*credits["indirect"]+stabilizers[m]*credits["stabilizer"] for m in set(direct)|set(indirect)|set(stabilizers)}
    clean=lambda d:{k:round(v,6) for k,v in sorted(d.items()) if v}
    return {"directSets":clean(direct),"indirectSets":clean(indirect),"stabilizerParticipationSets":clean(stabilizers),"effectiveSets":clean(effective),"movementPatternSets":clean(patterns),"muscles":{m:{"directSets":direct[m],"indirectSets":indirect[m],"stabilizerParticipationSets":stabilizers[m],"effectiveSets":effective[m]} for m in sorted(effective)},"movementPatterns":clean(patterns),"coverageCompleteness":{"actualCountedSets":counted,"mappedActualSets":mapped,"unmappedActualSets":unmapped,"ineligibleActualSets":ineligible,"mappedFraction":round(mapped/counted,6) if counted else 1.0}}

def _range_check(planned, actual):
    r=normalize_range(planned); a=float(actual)
    return {"plannedRange":r,"actual":a,"meetsMinimum":a>=r["min"],"meetsTarget":a>=r["target"],"withinMaximum":a<=r["max"],"differenceFromTarget":round(a-r["target"],6)}

def _value_check(planned, actual):
    if planned is None or actual is None: return {"planned":planned,"actual":actual,"delta":None,"withinRange":None,"comparable":False,"reason":"missing planned or actual value"}
    r=normalize_range(planned); a=float(actual)
    return {"planned":planned,"actual":a,"delta":round(a-r["target"],6),"withinRange":r["min"]<=a<=r["max"],"comparable":True}

def _load_check(planned, actual):
    if not planned or not actual: return {"planned":planned,"actual":actual,"delta":None,"withinRange":None,"comparable":False,"reason":"missing planned or actual load"}
    unit=planned.get("unit"); target=planned.get("value",planned.get("target")); lo=planned.get("min",target); hi=planned.get("max",target)
    if not unit or target is None: return {"planned":planned,"actual":actual,"delta":None,"withinRange":None,"comparable":False,"reason":"planned load has no comparable mass quantity"}
    try: av=normalize_quantity(actual,unit)
    except (UnitError,TypeError,ValueError) as e: return {"planned":planned,"actual":actual,"delta":None,"withinRange":None,"comparable":False,"reason":str(e)}
    return {"planned":planned,"actual":actual,"normalizedActual":{"value":round(av,6),"unit":unit},"delta":round(av-float(target),6),"withinRange":float(lo)-1e-6<=av<=float(hi)+1e-6,"comparable":True}

def _planned_volume_load(rx):
    if not rx: return None, "missing prescription"
    specs=rx.get("plannedSets")
    if specs is not None: specs=[item for item in specs if item.get("setType") in COUNTED_SET_TYPES]
    if specs is None:
        specs=[rx] * int(planned_set_range(rx)["target"])
    total=0.0
    for spec in specs:
        load=spec.get("load"); reps=spec.get("reps")
        if not load or reps is None or load.get("unit","").lower() not in {"kg","lb","g"}: return None, "planned load is not a comparable mass quantity"
        try: mass=normalize_quantity({"value":load.get("value",load.get("target")),"unit":load["unit"]},"kg")
        except (UnitError,TypeError,ValueError): return None, "planned load is not a comparable mass quantity"
        total += normalize_range(reps)["target"] * mass
    return total, None

def _planned_for_actual(rx, item, index, by_id, consumed):
    explicit=item.get("setPrescriptionId")
    if explicit is not None:
      candidate=by_id.get(explicit)
      if candidate is None or explicit in consumed: return None
      consumed.add(explicit); return candidate
    planned=rx.get("plannedSets",[]) if rx else []
    available=[p for p in planned if p["setPrescriptionId"] not in consumed]
    if index < len(planned) and planned[index]["setPrescriptionId"] not in consumed:
      p=planned[index]; consumed.add(p["setPrescriptionId"]); return p
    if len(available)==1:
      p=available[0]; consumed.add(p["setPrescriptionId"]); return p
    return None

def analyze_plan_actual(plan:dict[str,Any], workout:dict[str,Any], db:Any)->dict[str,Any]:
    matching=match_plan_actual(plan,workout); sid=matching.get("planSessionId"); session=next((s for s in plan.get("sessions",[]) if s.get("planSessionId")==sid),None)
    session_plan={**plan,"phases":[],"sessions":[session] if session else []}; planned=analyze_plan(session_plan,db) if session else None
    groups={"matched":[],"substitution":[],"unplanned":[]}
    for match in matching["exercises"]:
      key="unplanned" if match["status"] not in {"matched","substitution"} else match["status"]; groups[key].append(match["actual"])
    coverages={k:_metric_coverage(v,db) for k,v in groups.items()}; coverages["total"]=_metric_coverage([m["actual"] for m in matching["exercises"]],db)
    exercise_rows=[]; set_rows=[]
    for match in matching["exercises"]:
      rx=match.get("prescription"); actual=match["actual"]; counted=completed_exercise_sets(actual); prange=planned_set_range(rx) if rx else normalize_range(0)
      planned_items=rx.get("plannedSets",[]) if rx else []; by_id={p["setPrescriptionId"]:p for p in planned_items}; consumed=set(); reps_ok=0; comparisons=[]; planned_vl, vl_reason=_planned_volume_load(rx); actual_vl=0; vl_comparable=planned_vl is not None
      for index,item in enumerate(actual.get("sets",[])):
        pitem=_planned_for_actual(rx,item,index,by_id,consumed) if planned_items else None
        completed=item.get("completed") is True; counted_set=set_is_counted(item)
        if not completed: status="incomplete"
        elif planned_items and pitem is None: status="unable_to_match" if item.get("setPrescriptionId") else "unplanned_addition"
        else: status=match["status"]
        planned_spec=pitem or rx or {}; reps=planned_spec.get("reps"); repcheck=_value_check(reps,item.get("reps"))
        if counted_set and repcheck.get("withinRange"): reps_ok+=1
        loadcheck=_load_check(planned_spec.get("load"),item.get("load")); effort=planned_spec.get("effort") or {}
        rpecheck=_value_check(effort.get("rpe"),item.get("rpe")); rircheck=_value_check(effort.get("rir"),item.get("rir"))
        if counted_set and status in {"matched","substitution"}:
          if vl_comparable and item.get("load") and item.get("reps") is not None:
            try: actual_vl += float(item["reps"]) * normalize_quantity(item["load"], "kg")
            except (UnitError, TypeError, ValueError): vl_comparable=False; vl_reason="actual load is not a comparable mass quantity"
          elif vl_comparable: vl_comparable=False; vl_reason="missing actual reps or load"
        row={"actualExerciseIndex":match["actualExerciseIndex"],"setNumber":item.get("setNumber"),"prescriptionId":match.get("prescriptionId"),"setPrescriptionId":pitem.get("setPrescriptionId") if pitem else item.get("setPrescriptionId"),"status":status,"completed":completed,"counted":counted_set,"reps":repcheck,"load":loadcheck,"rpe":rpecheck,"rir":rircheck}; set_rows.append(row); comparisons.append(row)
      for pitem in planned_items:
        if pitem["setPrescriptionId"] not in consumed: set_rows.append({"actualExerciseIndex":match["actualExerciseIndex"],"setNumber":None,"prescriptionId":match.get("prescriptionId"),"setPrescriptionId":pitem["setPrescriptionId"],"status":"missing_prescription","completed":False,"counted":False})
      actual_count=len(counted); set_range=_range_check(prange,actual_count)
      vl={"planned":round(planned_vl,6) if vl_comparable else None,"actual":round(actual_vl,6) if vl_comparable else None,"delta":round(actual_vl-planned_vl,6) if vl_comparable else None,"fraction":round(actual_vl/planned_vl,6) if vl_comparable and planned_vl else None,"comparable":vl_comparable}
      if vl_reason: vl["reason"]=vl_reason
      exercise_rows.append({"actualExerciseIndex":match["actualExerciseIndex"],"prescriptionId":match.get("prescriptionId"),"plannedExerciseId":rx.get("exerciseId") if rx else None,"actualExerciseId":actual.get("exerciseId"),"status":match["status"],"plannedSets":prange["target"],"plannedSetRange":prange,"actualCompletedSets":actual_count,"setDelta":round(actual_count-prange["target"],6),"setRangeAdherence":set_range,"repsAdherentSets":reps_ok,"strictPrescriptionAdherence":match["status"]=="matched","substitutionAdjustedCompletion":match["status"] in {"matched","substitution"},"volumeLoad":vl})
    pn=planned["nativeCycle"] if planned else {}; ac=coverages["matched"]; sub=coverages["substitution"]
    muscle_rows={}
    metrics=(("direct","directSets"),("indirect","indirectSets"),("stabilizerParticipation","stabilizerParticipationSets"),("effective","effectiveSets"))
    muscles=set().union(*(set(pn.get(key,{}))|set(ac.get(key,{}))|set(sub.get(key,{})) for _,key in metrics))
    for m in sorted(muscles):
      detail={name:_adherence(pn.get(key,{}).get(m,0),ac.get(key,{}).get(m,0)+sub.get(key,{}).get(m,0)) for name,key in metrics}; detail.update(detail["effective"]); muscle_rows[m]=detail
    patterns={p:_adherence(pn.get("movementPatternSets",{}).get(p,0),ac["movementPatternSets"].get(p,0)+sub["movementPatternSets"].get(p,0)) for p in sorted(set(pn.get("movementPatternSets",{}))|set(ac["movementPatternSets"])|set(sub["movementPatternSets"]))}
    statuses=defaultdict(int)
    for row in exercise_rows: statuses[row["status"]]+=1
    statuses["missing_prescription"]=len(matching["missingPrescriptions"])
    md=_metadata(db)
    metadata={"analysisVersion":ANALYSIS_VERSION,"analysisPolicy":ANALYSIS_POLICY,"dbSchemaVersion":md.get("schemaVersion"),"dbConverterVersion":md.get("converterVersion"),"dbUpstreamSha256":md.get("upstream",{}).get("sha256"),"planSchemaVersion":plan.get("schemaVersion"),"workoutSchemaVersion":workout.get("schemaVersion"),"setCredits":set_credits(db),"nativePeriodDays":plan.get("cycle",{}).get("lengthDays"),"normalizedPeriodDays":7,"rangePolicy":RANGE_POLICY,"unitPolicy":UNIT_POLICY}
    return {"analysisVersion":ANALYSIS_VERSION,"analysisPolicy":ANALYSIS_POLICY,"analysisMetadata":metadata,"plan":{"planId":plan.get("planId"),"revisionId":plan.get("revisionId")},"actual":{"sessionId":workout.get("sessionId"),"schemaVersion":workout.get("schemaVersion")},"matching":{"sessionStatus":matching["sessionStatus"],"planSessionId":sid,"exerciseStatuses":dict(sorted(statuses.items())),"exercises":exercise_rows,"sets":set_rows,"missingPrescriptions":[x["prescriptionId"] for x in matching["missingPrescriptions"]]},"plannedCoverage":pn,"matchedActualCoverage":coverages["matched"],"unplannedActualCoverage":coverages["unplanned"],"totalActualCoverage":coverages["total"],"actualCoverage":coverages,"coverageCompleteness":{"plan":planned["coverageCompleteness"] if planned else {},"actual":coverages["total"]["coverageCompleteness"]},"adherence":{"muscles":muscle_rows,"movementPatterns":patterns}}

__all__=["analyze_plan_actual"]
