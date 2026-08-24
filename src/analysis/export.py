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
__all__=["plan_coverage_rows","plan_actual_rows","write_plan_coverage_csv","write_plan_actual_csv"]
