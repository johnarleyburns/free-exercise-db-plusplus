"""Deterministic tidy research exports for analysis results."""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Any

def _write(rows: list[dict[str, Any]], path: str | Path) -> None:
    fields=["kind","period","metric","key","planned","actual","delta","fraction"]
    with Path(path).open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)

def plan_coverage_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    rows=[]
    for period in ("nativeCycle","normalized7Day"):
        view=analysis.get(period,{})
        for metric in ("directSets","indirectSets","stabilizerParticipationSets","effectiveSets","movementPatternSets"):
            for key,value in sorted(view.get(metric,{}).items()):
                rows.append({"kind":"plan_coverage","period":period,"metric":metric,"key":key,"planned":value,"actual":"","delta":"","fraction":""})
    return rows

def plan_actual_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows=[]
    for kind, collection in (("muscle_adherence", result.get("adherence",{}).get("muscles",{})), ("pattern_adherence", result.get("adherence",{}).get("movementPatterns",{}))):
        for key,value in sorted(collection.items()):
            rows.append({"kind":kind,"period":"linked_session","metric":"adherence","key":key,"planned":value.get("planned"),"actual":value.get("actual"),"delta":value.get("delta"),"fraction":value.get("fraction")})
    return rows

def write_plan_coverage_csv(analysis: dict[str, Any], path: str | Path) -> None: _write(plan_coverage_rows(analysis),path)
def write_plan_actual_csv(result: dict[str, Any], path: str | Path) -> None: _write(plan_actual_rows(result),path)
__all__=["plan_coverage_rows","plan_actual_rows","write_plan_coverage_csv","write_plan_actual_csv","muscle_research_rows","exercise_research_rows","write_muscle_research_csv","write_exercise_research_csv"]


def muscle_research_rows(result: dict[str, Any], subject_id: str = "") -> list[dict[str, Any]]:
    """Deterministic muscle-level rows retaining ranged planned values."""
    md=result.get("analysisMetadata",{}); rows=[]
    plan=result.get("plan",{}); actual=result.get("actual",{})
    for muscle, values in sorted(result.get("adherence",{}).get("muscles",{}).items()):
        row={"subject_id":subject_id,"session_id":actual.get("sessionId", ""),"plan_id":plan.get("planId", ""),"revision_id":plan.get("revisionId", ""),"plan_session_id":result.get("matching",{}).get("planSessionId", ""),"phase_id":"","period":"linked_session","muscle":muscle,"analysis_policy":md.get("analysisPolicy",result.get("analysisPolicy","")),"db_schema_version":md.get("dbSchemaVersion",""),"db_converter_version":md.get("dbConverterVersion",""),"plan_schema_version":md.get("planSchemaVersion",""),"workout_schema_version":md.get("workoutSchemaVersion","")}
        for label,key in (("direct","direct"),("indirect","indirect"),("stabilizer","stabilizerParticipation"),("effective","effective")):
            metric=values.get(key,{})
            row[f"planned_{label}_sets"]=metric.get("planned",""); row[f"actual_{label}_sets"]=metric.get("actual","")
            planned_range=metric.get("plannedRange",values.get("plannedRanges",{}).get(key,{}))
            for bound in ("min","target","max"):
                value=planned_range.get(bound)
                row[f"planned_{label}_sets_{bound}"]="" if value is None else value
        row["effective_adherence_fraction"]=values.get("effective",values).get("fraction",""); rows.append(row)
    return rows

def exercise_research_rows(result: dict[str, Any], subject_id: str = "") -> list[dict[str, Any]]:
    rows=[]; actual=result.get("actual",{})
    for item in result.get("matching",{}).get("exercises",[]):
        rng=item.get("plannedSetRange",{})
        rows.append({"subject_id":subject_id,"session_id":actual.get("sessionId",""),"prescription_id":item.get("prescriptionId",""),"planned_exercise_id":item.get("plannedExerciseId",""),"actual_exercise_id":item.get("actualExerciseId",""),"match_status":item.get("status",""),"planned_sets_min":rng.get("min",""),"planned_sets_target":rng.get("target",item.get("plannedSets","")),"planned_sets_max":rng.get("max",""),"actual_sets":item.get("actualCompletedSets","")})
    return rows

def _write_research(rows: list[dict[str, Any]], path: str | Path) -> None:
    fields=list(rows[0]) if rows else []
    with Path(path).open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)

def write_muscle_research_csv(result: dict[str, Any], path: str | Path, subject_id: str = "") -> None: _write_research(muscle_research_rows(result,subject_id),path)
def write_exercise_research_csv(result: dict[str, Any], path: str | Path, subject_id: str = "") -> None: _write_research(exercise_research_rows(result,subject_id),path)
