"""Deterministic derived TrainingState for recent longitudinal facts."""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone as dt_timezone
from typing import Any
from .longitudinal import TrainingHistory, _activation, _parse_timestamp, _tz, analyze_periods, _scheduled
from ._analysis.plan_actual import analyze_plan_actual
from ._analysis.policies import completed_exercise_sets, planned_set_range, set_credits

STATE_VERSION = "0.1.0"
WINDOWS = {"last_7_days": 7, "last_28_days": 28}

def _doc(v): return v.document if hasattr(v, "document") else v
def _stamp(v, tz): return _parse_timestamp(v, tz)
def _dbmd(db): return db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
def _exercise(db, eid):
    try: return db.get_exercise(eid) if hasattr(db, "get_exercise") else db.get("exercises", {}).get(eid)
    except KeyError: return None
def _ann(x): return x.annotation if hasattr(x, "annotation") else (x or {}).get("annotation", {})

def _window(as_of, window, tz, active_plan=None, history=None, relationships=None):
    d = as_of.date()
    if isinstance(window, dict):
        start, end = date.fromisoformat(str(window["start"])[:10]), date.fromisoformat(str(window["end"])[:10])
    elif isinstance(window, (tuple, list)):
        start, end = date.fromisoformat(str(window[0])[:10]), date.fromisoformat(str(window[1])[:10])
    elif window in WINDOWS:
        start, end = d - timedelta(days=WINDOWS[window]-1), d
    elif window in {"current_plan_cycle", "current_phase"} and active_plan:
        activation = _activation(history, active_plan); anchor = date.fromisoformat(str(activation.get("effectiveFrom", as_of.date()))[:10]) if activation else d
        cycle = int(active_plan.get("cycle", {}).get("lengthDays", 7)); elapsed = max(0, (d-anchor).days)
        start = anchor + timedelta(days=(elapsed // cycle) * cycle); end = start + timedelta(days=cycle-1)
        if window == "current_phase":
            cursor = anchor
            for phase in active_plan.get("phases", []):
                length = int((phase.get("cycle") or active_plan.get("cycle") or {"lengthDays":cycle}).get("lengthDays", cycle)) * int(phase.get("durationCycles", 1))
                if cursor <= d < cursor + timedelta(days=length): start, end = cursor, cursor + timedelta(days=length-1); break
                cursor += timedelta(days=length)
    else: raise ValueError("window must be last_7_days, last_28_days, current_plan_cycle, current_phase, or a custom date range")
    if end > d: end = d
    if start > end: raise ValueError("history window start must not be after end")
    return start, end

def _active(history, as_of):
    candidates=[]
    for plan in history.plans:
        active=_activation(history, plan)
        if active and active.get("effectiveFrom"):
            begin=_stamp(active["effectiveFrom"], as_of.tzinfo); finish=_stamp(active["effectiveTo"], as_of.tzinfo) if active.get("effectiveTo") else None
            if begin <= as_of and (finish is None or as_of < finish): candidates.append(plan)
    if len(candidates)>1: raise ValueError("overlapping plan activation windows")
    if candidates: return candidates[0]
    # With no activation metadata, an explicit plan reference in a recent
    # observation is the only applicable context; do not choose by recency.
    referenced = {((w.get("planReference") or {}).get("planId"), ((w.get("planReference") or {}).get("revisionId")))
                  for w in history.workouts if w.get("startTime") and _stamp(w["startTime"], as_of.tzinfo) <= as_of}
    matches = [p for p in history.plans if (p.get("planId"), p.get("revisionId")) in referenced]
    return matches[0] if len(matches) == 1 else None

def derive_training_state(history, db, *, as_of, window="last_28_days", relationships=None, target=None, timezone=None):
    """Derive a serializable state. ``as_of`` is required and no clock is read."""
    if not isinstance(history, TrainingHistory): raise TypeError("history must be TrainingHistory")
    tz = timezone or getattr(as_of, "tzinfo", None) or "UTC"; asof = _stamp(as_of, tz)
    active = _active(history, asof); start, end = _window(asof, window, tz, active, history)
    analysis_history = history if not target or history.targets else TrainingHistory(history.subject_id, history.plans, history.workouts, [target], history.plan_activations, history.metadata)
    analysis = analyze_periods(analysis_history, db, "custom_date_range", start=start, end=end, timezone=tz)
    plan_context = {"planId": active.get("planId"), "revisionId": active.get("revisionId")} if active else {"planId": None, "revisionId": None}
    if active:
        activation=_activation(history, active); plan_context["phaseId"] = None
        if active.get("phases"):
            elapsed=(end-date.fromisoformat(str(activation.get("effectiveFrom", start))[:10])).days if activation else 0; cursor=0
            for p in active["phases"]:
                length=int((p.get("cycle") or active.get("cycle") or {"lengthDays":7}).get("lengthDays",7))*int(p.get("durationCycles",1))
                if cursor <= elapsed < cursor+length: plan_context["phaseId"]=p.get("phaseId"); break
                cursor += length
        plan_context["cyclePosition"] = ((end-date.fromisoformat(str((activation or {}).get("effectiveFrom", start))[:10])).days % int(active.get("cycle",{}).get("lengthDays",7))) + 1
        cycle_length=int(active.get("cycle",{}).get("lengthDays",7)); occ=[o for o in _scheduled(active,asof.date(),asof.date()+timedelta(days=cycle_length),history,"custom_date_range",_tz(tz)) if o.scheduled_date >= asof.date()]
        plan_context["nextScheduledOccurrence"] = next(({"scheduledDate":o.scheduled_date.isoformat(),"planSessionId":o.plan_session_id} for o in occ if o.scheduled_date >= asof.date()), None)
    exids=set()
    if active: exids.update(rx.get("exerciseId") for s in active.get("sessions",[]) for rx in s.get("exercises",[]) if rx.get("exerciseId"))
    for w in history.workouts:
        if w.get("startTime") and start <= _stamp(w["startTime"],tz).date() <= end and _stamp(w["startTime"],tz) <= asof: exids.update(e.get("exerciseId") for e in w.get("exercises",[]) if e.get("exerciseId"))
    states={}
    for eid in sorted(exids):
        prescribed=[rx for s in (active or {}).get("sessions",[]) for rx in s.get("exercises",[]) if rx.get("exerciseId")==eid]
        observations=[]
        for w in history.workouts:
            if not w.get("startTime") or not start <= _stamp(w["startTime"],tz).date() <= end or _stamp(w["startTime"],tz)>asof: continue
            for e in w.get("exercises",[]):
                if e.get("exerciseId")==eid: observations.append((w,e))
        observations.sort(key=lambda x: (_stamp(x[0]["startTime"],tz), x[0].get("sessionId", "")))
        matched=[x for x in observations if active and (x[0].get("planReference") or {}).get("revisionId")==active.get("revisionId")]
        last=(matched or observations)[-1] if (matched or observations) else None; actual=completed_exercise_sets(last[1]) if last else []
        last_rx=next((rx for w,e in reversed(matched) for rx in prescribed if rx.get("prescriptionId")==e.get("exercisePrescriptionId")), prescribed[0] if prescribed else None)
        states[eid]={"exerciseId":eid,"lastPerformedAt":last[0].get("startTime") if last else None,"lastPrescription":last_rx,"lastActual":{"exerciseId":eid,"sets":actual} if last else None,"recentSessionCount":len(observations),"recentCompletedSetCount":sum(len(completed_exercise_sets(e)) for _,e in observations),"recentReps":[x.get("reps") for x in actual if x.get("reps") is not None],"recentLoads":[x.get("load") for x in actual if x.get("load") is not None],"recentRPE":[x.get("rpe") for x in actual if x.get("rpe") is not None],"recentRIR":[x.get("rir") for x in actual if x.get("rir") is not None],"recentSetTypes":[x.get("setType") for x in actual],"substitutionCount":sum(1 for w,e in observations if e.get("substitution")),"unplannedCount":sum(1 for w,e in observations if not e.get("exercisePrescriptionId")),"prescriptionAdherence":None}
    families={}
    if relationships:
        for eid in sorted(states):
            fam=relationships.family_for(eid) if hasattr(relationships,"family_for") else None
            if fam: families.setdefault(fam.family_id,{"familyId":fam.family_id,"recentExerciseIds":[],"mostRecentExerciseId":None,"explicitSubstitutionCount":0,"variantHistory":[]})["recentExerciseIds"].append(eid)
        for f in families.values():
            f["recentExerciseIds"].sort(); f["mostRecentExerciseId"]=max(f["recentExerciseIds"], key=lambda x: states[x]["lastPerformedAt"] or "") if f["recentExerciseIds"] else None
            f["explicitSubstitutionCount"]=sum(states[x]["substitutionCount"] for x in f["recentExerciseIds"])
    prov={"stateVersion":STATE_VERSION,"analysisVersion":analysis.get("analysisVersion"),"analysisPolicy":analysis.get("analysisPolicy"),"historyWindow":{"type":window,"start":start.isoformat(),"end":end.isoformat()},"asOf":asof.isoformat(),"timezone":str(tz),"dbSchemaVersion":_dbmd(db).get("schemaVersion"),"dbConverterVersion":_dbmd(db).get("converterVersion"),"dbUpstreamSha256":(_dbmd(db).get("upstream") or {}).get("sha256"),"setCredits":set_credits(db),"planSchemaVersions":sorted({p.get("schemaVersion") for p in history.plans if p.get("schemaVersion")}),"workoutSchemaVersions":sorted({w.get("schemaVersion") for w in history.workouts if w.get("schemaVersion")}),"targetSchemaVersion":target.get("schemaVersion") if target else None,"relationshipSchemaVersion":relationships.document.get("schemaVersion") if hasattr(relationships,"document") else (relationships.get("schemaVersion") if relationships else None),"workoutCount":len(history.workouts),"mappedFraction":analysis.get("periods", [{}])[0].get("mappedFraction") if analysis.get("periods") else None}
    muscle={}
    for row in analysis.get("musclePeriodRows",[]):
        m=muscle.setdefault(row["muscle"],{"muscleId":row["muscle"]}); m.update({"directSets":row.get("actual_direct",0),"indirectSets":row.get("actual_indirect",0),"stabilizerSets":row.get("actual_stabilizer",0),"effectiveSets":row.get("actual_effective",0),"exposures":row.get("actual_exposures",0),"mappedFraction":row.get("mapped_fraction")})
        if target: m["targetState"]=row.get("target_state"); m["plannedVsActual"]={"planned":row.get("planned_effective_target"),"actual":row.get("actual_effective")}
    sessions=analysis.get("sessionRows",[]); exercises=analysis.get("exerciseRows",[])
    return {"stateVersion":STATE_VERSION,"subjectId":history.subject_id,"asOf":asof.isoformat(),"historyWindow":prov["historyWindow"],"activePlan":plan_context,"exerciseState":states,"familyState":families,"muscleState":muscle,"adherenceState":{"sessionAdherence":sessions,"exercisePrescriptionAdherence":exercises,"substitutionAdjustedCompletion":sum(1 for x in exercises if x.get("match_status") in {"matched","substitution"}),"missedScheduledOccurrences":[x for x in sessions if x.get("session_status")=="missed_planned_session"],"repeatedSkippedExercises":sorted({x.get("prescription_id") for x in exercises if x.get("match_status")=="missing_prescription"}),"repeatedSubstitutions":sorted({x.get("planned_exercise_id") for x in exercises if x.get("match_status")=="substitution"}),"unplannedExercises":[x for x in exercises if x.get("match_status")=="unplanned_addition"],"unplannedSets":sum(x.get("unplanned_sets",0) for x in sessions)},"sessionState":sessions,"provenance":prov}

__all__=["derive_training_state","STATE_VERSION"]
