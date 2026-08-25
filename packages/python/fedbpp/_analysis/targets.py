"""Compare normalized PLAN coverage with a Volume TARGET profile."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
from .coverage import analyze_plan

ROOT = Path(__file__).resolve().parents[1] / "schemas"


def _range(target: Any) -> tuple[float | None, float | None, float | None]:
    if isinstance(target, (int, float)):
        value = float(target); return value, value, value
    return (target.get("min"), target.get("target"), target.get("max"))


def validate_target(target: dict[str, Any], schema_path: str | Path | None = None, *, db: Any | None = None) -> list[str]:
    from jsonschema import Draft202012Validator
    schema_file = Path(schema_path) if schema_path else ROOT / "volume-target.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    errors = [f"{'.'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}" for error in Draft202012Validator(schema).iter_errors(target)]
    if not errors and isinstance(target, dict):
        for muscle, value in target.get("muscles", {}).items():
            if "min" in value and "max" in value and value["min"] > value["max"]:
                errors.append(f"muscles.{muscle}: min must not exceed max")
            if "target" in value and "min" in value and value["target"] < value["min"]:
                errors.append(f"muscles.{muscle}: target must not be below min")
            if "target" in value and "max" in value and value["target"] > value["max"]:
                errors.append(f"muscles.{muscle}: target must not exceed max")
    if not errors and db is not None:
        metadata = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
        ontology = metadata.get("muscleOntology") or metadata.get("muscles")
        if ontology is None:
            ontology = {m for ex in (db.exercises.values() if hasattr(db, "exercises") else db.get("exercises", {}).values()) for role in ("direct", "indirect", "stabilizers") for m in ((ex.annotation if hasattr(ex, "annotation") else ex.get("annotation", {})).get(role, []))}
        known = set(ontology.keys() if isinstance(ontology, dict) else ontology)
        for muscle in target.get("muscles", {}):
            if muscle not in known: errors.append(f"muscles.{muscle}: unknown DB++ muscle ID")
    return sorted(errors)

def compare_to_targets(plan: dict[str, Any], target_profile: dict[str, Any], db: Any) -> dict[str, Any]:
    analysis = analyze_plan(plan, db)
    cycle_days = analysis["analysisMetadata"]["nativePeriodDays"]
    period_days = int(target_profile["periodDays"])
    scale = period_days / cycle_days
    effective = analysis["nativeCycle"]["effectiveSets"]
    effective_ranges = analysis["nativeCycle"].get("effectiveSetRanges", {})
    results: dict[str, Any] = {}
    configured = target_profile.get("muscles", {})
    for muscle in sorted(set(configured) | set(effective)):
        target = configured.get(muscle)
        minimum, desired, maximum = _range(target) if target is not None else (None, None, None)
        actual = round(float(effective.get(muscle, 0.0)) * scale, 6)
        if target is None: state = "not_targeted"
        elif minimum is not None and actual < minimum: state = "below_minimum"
        elif maximum is not None and actual > maximum: state = "above_maximum"
        elif desired is None: state = "within_range"
        elif actual < desired: state = "within_range_below_target"
        elif actual > desired: state = "within_range_above_target"
        else: state = "at_target"
        results[muscle] = {
            "actualEffectiveSets": actual,
            "minimum": minimum, "target": desired, "maximum": maximum,
            "min": minimum, "max": maximum, "differenceFromTarget": round(actual - desired, 6) if desired is not None else None,
            "planEffectiveSetRange": {key: round(value * scale, 6) for key, value in effective_ranges.get(muscle, {"min": actual / scale if scale else 0, "target": actual / scale if scale else 0, "max": actual / scale if scale else 0}).items()},
            "state": state,
            "periodDays": period_days,
        }
    return {
        "analysisVersion": "0.1.0",
        "plan": analysis["plan"],
        "target": {"targetId": target_profile.get("targetId"), "periodDays": period_days},
        "analysisPolicy": analysis["analysisPolicy"],
        "analysisMetadata": {**analysis["analysisMetadata"], "targetSchemaVersion": target_profile.get("schemaVersion"), "comparisonPeriodDays": period_days},
        "coverageCompleteness": analysis["coverageCompleteness"],
        "muscles": results,
    }

__all__ = ["compare_to_targets", "validate_target"]
