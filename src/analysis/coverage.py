"""Deterministic, range-aware PLAN coverage analysis."""
from __future__ import annotations
from collections import defaultdict
from typing import Any
from .policies import ANALYSIS_POLICY, ANALYSIS_VERSION, RANGE_POLICY, UNIT_POLICY, add_ranges, normalize_range, planned_set_range, representative_scalar, scale_range, set_credits

def _exercise(db, exercise_id): return db.get_exercise(exercise_id) if hasattr(db, "get_exercise") else db["exercises"][exercise_id]
def _annotation(exercise): return exercise.annotation if hasattr(exercise, "annotation") else exercise.get("annotation", {})
def _metadata(db): return db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
def _clean_range(value): return {k: round(v, 6) if v is not None else None for k,v in normalize_range(value).items()}
def _clean_ranges(values): return {k:_clean_range(v) for k,v in sorted(values.items()) if any(x not in (None, 0) for x in normalize_range(v).values())}
def _targets(values): return {k:round(representative_scalar(v),6) for k,v in sorted(values.items()) if representative_scalar(v) != 0}
def _add(table, key, value): table[key] = add_ranges(table.get(key, 0), value)

def _provenance(plan, db, days):
    md=_metadata(db); upstream=md.get("upstream", {})
    return {"analysisVersion":ANALYSIS_VERSION,"analysisPolicy":ANALYSIS_POLICY,"dbSchemaVersion":md.get("schemaVersion"),"dbConverterVersion":md.get("converterVersion"),"dbUpstreamSha256":upstream.get("sha256"),"planSchemaVersion":plan.get("schemaVersion"),"setCredits":set_credits(db),"nativePeriodDays":days,"normalizedPeriodDays":7,"rangePolicy":RANGE_POLICY,"unitPolicy":UNIT_POLICY}

def _single(plan, db, cycle_days):
    roles=[defaultdict(lambda:normalize_range(0)) for _ in range(4)]; direct,indirect,stabilizers,patterns=roles
    planned=mapped=unmapped=ineligible=normalize_range(0); unmapped_ids=[]; ineligible_ids=[]
    muscle_sessions=defaultdict(set); pattern_sessions=defaultdict(set)
    for session in plan.get("sessions", []):
      sid=session.get("planSessionId")
      for rx in session.get("exercises", []):
        sets=planned_set_range(rx); planned=add_ranges(planned,sets); eid=rx.get("exerciseId")
        try: ex=_exercise(db,eid) if eid else None
        except (KeyError,TypeError): ex=None
        if ex is None: unmapped=add_ranges(unmapped,sets); unmapped_ids.append(rx.get("prescriptionId")); continue
        mapped=add_ranges(mapped,sets); ann=_annotation(ex)
        if not ann.get("volumeEligible",False): ineligible=add_ranges(ineligible,sets); ineligible_ids.append(rx.get("prescriptionId")); continue
        for muscle in ann.get("direct",[]): _add(direct,muscle,sets); muscle_sessions[muscle].add(sid)
        for muscle in ann.get("indirect",[]): _add(indirect,muscle,sets); muscle_sessions[muscle].add(sid)
        for muscle in ann.get("stabilizers",[]): _add(stabilizers,muscle,sets)
        for pattern in ann.get("patterns",[]): _add(patterns,pattern,sets); pattern_sessions[pattern].add(sid)
    credits=set_credits(db); effective={}
    for m in set(direct)|set(indirect)|set(stabilizers):
      effective[m]=add_ranges(add_ranges(scale_range(direct[m],credits["direct"]),scale_range(indirect[m],credits["indirect"])),scale_range(stabilizers[m],credits["stabilizer"]))
    def view(scale=1):
      tables=(direct,indirect,stabilizers,effective,patterns); names=("directSetRanges","indirectSetRanges","stabilizerParticipationSetRanges","effectiveSetRanges","movementPatternSetRanges")
      out={name:_clean_ranges({k:scale_range(v,scale) for k,v in table.items()}) for name,table in zip(names,tables)}
      out.update({"directSets":_targets(out["directSetRanges"]),"indirectSets":_targets(out["indirectSetRanges"]),"stabilizerParticipationSets":_targets(out["stabilizerParticipationSetRanges"]),"effectiveSets":_targets(out["effectiveSetRanges"]),"movementPatternSets":_targets(out["movementPatternSetRanges"])})
      return out
    scale=7/cycle_days
    planned_scalar=representative_scalar(planned); mapped_scalar=representative_scalar(mapped)
    completeness={"plannedSets":round(planned_scalar,6),"plannedSetRange":_clean_range(planned),"mappedSets":round(mapped_scalar,6),"mappedSetRange":_clean_range(mapped),"unmappedSets":round(representative_scalar(unmapped),6),"unmappedSetRange":_clean_range(unmapped),"ineligibleSets":round(representative_scalar(ineligible),6),"ineligibleSetRange":_clean_range(ineligible),"mappedFraction":round(mapped_scalar/planned_scalar,6) if planned_scalar else 1.0,"unmappedPrescriptions":sorted(x for x in unmapped_ids if x),"ineligiblePrescriptions":sorted(x for x in ineligible_ids if x)}
    frequency={"muscles":{m:{"exposuresPerNativeCycle":len(s),"normalizedExposuresPer7Days":round(len(s)*scale,6)} for m,s in sorted(muscle_sessions.items())},"movementPatterns":{p:{"exposuresPerNativeCycle":len(s),"normalizedExposuresPer7Days":round(len(s)*scale,6)} for p,s in sorted(pattern_sessions.items())}}
    return completeness,{"periodDays":cycle_days,**view()},{"periodDays":7,**view(scale)},frequency

def analyze_plan(plan: dict[str,Any], db: Any)->dict[str,Any]:
    root_days=int(plan["cycle"]["lengthDays"]); completeness,native,normalized,frequency=_single(plan,db,root_days)
    result={"analysisVersion":ANALYSIS_VERSION,"analysisPolicy":ANALYSIS_POLICY,"plan":{"planId":plan.get("planId"),"revisionId":plan.get("revisionId")},"analysisMetadata":_provenance(plan,db,root_days),"coverageCompleteness":completeness,"nativeCycle":native,"normalized7Day":normalized,"exposureFrequency":frequency}
    phases=plan.get("phases",[])
    if phases:
      phase_results=[]
      for phase in phases:
        days=int((phase.get("cycle") or {}).get("lengthDays",root_days)); sessions=[s for s in plan.get("sessions",[]) if s.get("phaseId")==phase.get("phaseId")]
        sub={**plan,"phases":[],"sessions":sessions,"cycle":{"lengthDays":days}}; a=analyze_plan(sub,db)
        phase_results.append({"phaseId":phase["phaseId"],"durationCycles":phase["durationCycles"],"nativeCycle":a["nativeCycle"],"normalized7Day":a["normalized7Day"],"coverageCompleteness":a["coverageCompleteness"]})
      muscles=sorted({m for p in phase_results for m in p["normalized7Day"]["effectiveSetRanges"]}); weights=sum(p["durationCycles"] for p in phase_results)
      def agg(m,key):
        vals=[normalize_range(p["normalized7Day"]["effectiveSetRanges"].get(m,0))[key] for p in phase_results]
        return None if any(v is None for v in vals) else round(sum(v*p["durationCycles"] for v,p in zip(vals,phase_results))/weights,6)
      result["periodization"]={"phases":phase_results,"effectiveSetsByPhase":{p["phaseId"]:p["nativeCycle"]["effectiveSets"] for p in phase_results},"effectiveSetRangesByPhase":{p["phaseId"]:p["nativeCycle"]["effectiveSetRanges"] for p in phase_results},"normalizedEffectiveSetRangesDurationWeightedAverage":{m:{k:agg(m,k) for k in ("min","target","max")} for m in muscles},"effectiveSetsMinByMuscle":{m:min(p["nativeCycle"]["effectiveSets"].get(m,0) for p in phase_results) for m in muscles},"effectiveSetsMaxByMuscle":{m:max(p["nativeCycle"]["effectiveSets"].get(m,0) for p in phase_results) for m in muscles},"effectiveSetsAverageByMuscle":{m:representative_scalar({k:agg(m,k) for k in ("min","target","max")}) for m in muscles}}
    return result
