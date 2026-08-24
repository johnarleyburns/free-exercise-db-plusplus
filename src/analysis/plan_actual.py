"""PLAN-vs-ACTUAL adherence analysis."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .coverage import analyze_plan
from .matching import match_plan_actual

def _sets(value: Any) -> float:
    if isinstance(value, (int, float)): return float(value)
    for key in ("target", "min", "max"):
        if key in value: return float(value[key])
    return 0.0

def _exercise(db: Any, exercise_id: str) -> Any:
    return db.get_exercise(exercise_id) if hasattr(db, "get_exercise") else db["exercises"][exercise_id]

def _annotation(exercise: Any) -> dict[str, Any]:
    return exercise.annotation if hasattr(exercise, "annotation") else exercise.get("annotation", {})

def _coverage_for_actual(workout: dict[str, Any], matches: list[dict[str, Any]], db: Any) -> dict[str, dict[str, float]]:
    direct, indirect, stabilizers, patterns = (defaultdict(float) for _ in range(4))
    for match in matches:
        if match["status"] not in {"matched", "substitution"}: continue
        actual = match["actual"]; exercise_id = actual.get("exerciseId")
        if not exercise_id: continue
        try: ann = _annotation(_exercise(db, exercise_id))
        except KeyError: continue
        completed = sum(1 for item in actual.get("sets", []) if item.get("completed") is True)
        for muscle in ann.get("direct", []): direct[muscle] += completed
        for muscle in ann.get("indirect", []): indirect[muscle] += completed
        for muscle in ann.get("stabilizers", []): stabilizers[muscle] += completed
        for pattern in ann.get("patterns", []): patterns[pattern] += completed
    muscles = {}
    for muscle in sorted(set(direct) | set(indirect) | set(stabilizers)):
        muscles[muscle] = {"directSets": direct[muscle], "indirectSets": indirect[muscle], "stabilizerParticipationSets": stabilizers[muscle], "effectiveSets": direct[muscle] + indirect[muscle] * 0.5}
    return {"muscles": muscles, "movementPatterns": {key: patterns[key] for key in sorted(patterns)}}

def _adherence(planned: float, actual: float) -> dict[str, float | None]:
    return {"planned": round(planned, 6), "actual": round(actual, 6), "delta": round(actual - planned, 6), "fraction": round(actual / planned, 6) if planned else None}

def analyze_plan_actual(plan: dict[str, Any], workout: dict[str, Any], db: Any) -> dict[str, Any]:
    """Return deterministic matching and adherence results for one linked ACTUAL session."""
    matching = match_plan_actual(plan, workout)
    linked_session = matching.get("planSessionId")
    planned_session = next((session for session in plan.get("sessions", []) if session.get("planSessionId") == linked_session), None)
    session_plan = {**plan, "sessions": [planned_session] if planned_session else []}
    planned_coverage = analyze_plan(session_plan, db) if planned_session else None
    actual_coverage = _coverage_for_actual(workout, matching["exercises"], db)
    exercise_rows=[]; set_rows=[]
    for match in matching["exercises"]:
        prescription=match.get("prescription"); actual=match["actual"]
        actual_sets=[item for item in actual.get("sets", []) if item.get("completed") is True]
        planned_sets=_sets(prescription.get("sets")) if prescription else 0.0
        reps_adherent=0
        if prescription and prescription.get("reps") is not None:
            reps=prescription["reps"]
            for item in actual_sets:
                value=item.get("reps")
                if value is None: continue
                if isinstance(reps,(int,float)): ok=value == reps
                else: ok=all(("min" not in reps or value >= reps["min"], "target" not in reps or True, "max" not in reps or value <= reps["max"]))
                reps_adherent += int(ok)
        exercise_rows.append({"actualExerciseIndex":match["actualExerciseIndex"],"prescriptionId":match.get("prescriptionId"),"status":match["status"],"plannedSets":planned_sets,"actualCompletedSets":len(actual_sets),"setDelta":round(len(actual_sets)-planned_sets,6),"repsAdherentSets":reps_adherent})
        for item in actual.get("sets", []):
            set_rows.append({"actualExerciseIndex":match["actualExerciseIndex"],"setNumber":item.get("setNumber"),"prescriptionId":match.get("prescriptionId"),"status":match["status"],"completed":item.get("completed") is True})
    planned_muscles=(planned_coverage["nativeCycle"]["effectiveSets"] if planned_coverage else {})
    actual_muscles=actual_coverage["muscles"]
    muscle_rows={}
    for muscle in sorted(set(planned_muscles)|set(actual_muscles)):
        muscle_rows[muscle]=_adherence(float(planned_muscles.get(muscle,0)),float(actual_muscles.get(muscle,{}).get("effectiveSets",0)))
    planned_patterns=(planned_coverage["nativeCycle"]["movementPatternSets"] if planned_coverage else {})
    pattern_rows={pattern:_adherence(float(planned_patterns.get(pattern,0)),float(actual_coverage["movementPatterns"].get(pattern,0))) for pattern in sorted(set(planned_patterns)|set(actual_coverage["movementPatterns"]))}
    statuses=defaultdict(int)
    for row in exercise_rows: statuses[row["status"]]+=1
    statuses["missing_prescription"]=len(matching["missingPrescriptions"])
    return {"analysisVersion":"0.1.0","plan":{"planId":plan.get("planId"),"revisionId":plan.get("revisionId")},"actual":{"sessionId":workout.get("sessionId"),"schemaVersion":workout.get("schemaVersion")},"matching":{"sessionStatus":matching["sessionStatus"],"planSessionId":linked_session,"exerciseStatuses":dict(sorted(statuses.items())),"exercises":exercise_rows,"sets":set_rows,"missingPrescriptions":[row["prescriptionId"] for row in matching["missingPrescriptions"]]},"adherence":{"muscles":muscle_rows,"movementPatterns":pattern_rows}}

__all__=["analyze_plan_actual"]
