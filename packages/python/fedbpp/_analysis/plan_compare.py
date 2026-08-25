"""Deterministic PLAN-vs-PLAN comparison and tidy CSV export."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .coverage import analyze_plan


def _delta(a: float, b: float) -> float:
    return round(b - a, 6)

def _metric_rows(a: dict[str, float], b: dict[str, float]) -> dict[str, dict[str, float]]:
    return {
        key: {"planA": round(float(a.get(key, 0.0)), 6), "planB": round(float(b.get(key, 0.0)), 6),
              "delta": _delta(float(a.get(key, 0.0)), float(b.get(key, 0.0)))}
        for key in sorted(set(a) | set(b))
    }

def _range_metric_rows(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    result={}
    for metric in ("directSetRanges","indirectSetRanges","stabilizerParticipationSetRanges","effectiveSetRanges","movementPatternSetRanges"):
        result[metric]={}
        for key in sorted(set(a.get(metric,{}))|set(b.get(metric,{}))):
            ar=a.get(metric,{}).get(key,{"min":0,"target":0,"max":0}); br=b.get(metric,{}).get(key,{"min":0,"target":0,"max":0})
            result[metric][key]={bound:_optional_metric(ar.get(bound),br.get(bound)) for bound in ("min","target","max")}
    return result

def _optional_metric(a: float | None, b: float | None) -> dict[str, float | None]:
    return {"planA":a,"planB":b,"delta":round(b-a,6) if a is not None and b is not None else None}

def _exposure_rows(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    result={}
    for key in sorted(set(a)|set(b)):
        av=a.get(key,{}); bv=b.get(key,{})
        result[key]={
            "exposuresPerNativeCycle":_optional_metric(av.get("exposuresPerNativeCycle",0),bv.get("exposuresPerNativeCycle",0)),
            "normalizedExposuresPer7Days":_optional_metric(av.get("normalizedExposuresPer7Days",0),bv.get("normalizedExposuresPer7Days",0)),
        }
    return result

def _frequency(plan: dict[str, Any]) -> dict[str, Any]:
    sessions = plan.get("sessions", [])
    exercise_counts: dict[str, int] = {}
    for session in sessions:
        for prescription in session.get("exercises", []):
            key = prescription.get("exerciseId") or f"custom:{prescription.get('exerciseName', prescription['prescriptionId'])}"
            exercise_counts[key] = exercise_counts.get(key, 0) + 1
    return {"sessions": len(sessions), "exercisePrescriptions": sum(exercise_counts.values()), "exercises": dict(sorted(exercise_counts.items()))}

def compare_plans(plan_a: dict[str, Any], plan_b: dict[str, Any], db: Any) -> dict[str, Any]:
    """Compare two PLAN revisions without linking either to ACTUAL observations."""
    analysis_a = analyze_plan(plan_a, db)
    analysis_b = analyze_plan(plan_b, db)
    native_a, native_b = analysis_a["nativeCycle"], analysis_b["nativeCycle"]
    normalized_a, normalized_b = analysis_a["normalized7Day"], analysis_b["normalized7Day"]
    native = {metric: _metric_rows(native_a[metric], native_b[metric]) for metric in ("directSets", "indirectSets", "stabilizerParticipationSets", "effectiveSets", "movementPatternSets")}
    native["ranges"] = _range_metric_rows(native_a, native_b)
    normalized = {metric: _metric_rows(normalized_a[metric], normalized_b[metric]) for metric in ("directSets", "indirectSets", "stabilizerParticipationSets", "effectiveSets", "movementPatternSets")}
    normalized["ranges"] = _range_metric_rows(normalized_a, normalized_b)
    freq_a, freq_b = _frequency(plan_a), _frequency(plan_b)
    exercise_frequency = _metric_rows(freq_a["exercises"], freq_b["exercises"])
    exposure_a, exposure_b = analysis_a["exposureFrequency"], analysis_b["exposureFrequency"]
    metadata_a, metadata_b = analysis_a["analysisMetadata"], analysis_b["analysisMetadata"]
    common_fields=("analysisVersion","analysisPolicy","dbSchemaVersion","dbConverterVersion","dbUpstreamSha256","setCredits","rangePolicy","unitPolicy")
    metadata={field:metadata_a.get(field) if metadata_a.get(field)==metadata_b.get(field) else {"planA":metadata_a.get(field),"planB":metadata_b.get(field)} for field in common_fields}
    metadata.update({"planSchemaVersions":{"planA":metadata_a.get("planSchemaVersion"),"planB":metadata_b.get("planSchemaVersion")},"normalizedPeriodDays":7,"nativePeriodDays":{"planA":native_a["periodDays"],"planB":native_b["periodDays"]}})
    return {
        "comparisonVersion": "0.1.0",
        "plans": {
            "planA": {"planId": plan_a.get("planId"), "revisionId": plan_a.get("revisionId")},
            "planB": {"planId": plan_b.get("planId"), "revisionId": plan_b.get("revisionId")},
        },
        "analysisMetadata": metadata,
        "nativeCycle": native,
        "normalized7Day": normalized,
        "frequency": {
            "sessions": {"planA": freq_a["sessions"], "planB": freq_b["sessions"], "delta": freq_b["sessions"] - freq_a["sessions"]},
            "exercisePrescriptions": {"planA": freq_a["exercisePrescriptions"], "planB": freq_b["exercisePrescriptions"], "delta": freq_b["exercisePrescriptions"] - freq_a["exercisePrescriptions"]},
            "exercises": exercise_frequency,
            "muscles": _exposure_rows(exposure_a.get("muscles",{}),exposure_b.get("muscles",{})),
            "movementPatterns": _exposure_rows(exposure_a.get("movementPatterns",{}),exposure_b.get("movementPatterns",{})),
        },
        "coverageCompleteness": {"planA": analysis_a["coverageCompleteness"], "planB": analysis_b["coverageCompleteness"]},
    }

def tidy_rows(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic long-form rows suitable for CSV or data frames."""
    rows: list[dict[str, Any]] = []
    for period in ("nativeCycle", "normalized7Day"):
        for metric in ("directSets", "indirectSets", "stabilizerParticipationSets", "effectiveSets", "movementPatternSets"):
            for key, values in comparison[period][metric].items():
                rows.append({"kind": "volume", "period": period, "metric": metric, "key": key, **values})
    for metric in ("sessions", "exercisePrescriptions"):
        values = comparison["frequency"][metric]
        rows.append({"kind": "frequency", "period": "native", "metric": metric, "key": "", **values})
    for key, values in comparison["frequency"]["exercises"].items():
        rows.append({"kind": "frequency", "period": "native", "metric": "exercisePrescriptions", "key": key, **values})
    for metric in ("muscles","movementPatterns"):
        for key, periods in comparison["frequency"][metric].items():
            for period, values in periods.items():
                rows.append({"kind":"frequency","period":period,"metric":metric,"key":key,**values})
    return rows

def write_json(comparison: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_tidy_csv(comparison: dict[str, Any], path: str | Path) -> None:
    rows = tidy_rows(comparison)
    fields = ["kind", "period", "metric", "key", "planA", "planB", "delta"]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

__all__ = ["compare_plans", "tidy_rows", "write_json", "write_tidy_csv"]
