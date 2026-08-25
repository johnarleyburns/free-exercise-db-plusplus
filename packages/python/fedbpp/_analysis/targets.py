"""Compare normalized PLAN coverage with a Volume TARGET profile."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
from .coverage import analyze_plan

ROOT = Path(__file__).resolve().parents[2]


def _range(target: Any) -> tuple[float | None, float | None, float | None]:
    if isinstance(target, (int, float)):
        value = float(target); return value, value, value
    return (target.get("min"), target.get("target"), target.get("max"))


def validate_target(target: dict[str, Any], schema_path: str | Path | None = None) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError("validation requires the jsonschema package") from exc
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
    return sorted(errors)

def compare_to_targets(plan: dict[str, Any], target_profile: dict[str, Any], db: Any) -> dict[str, Any]:
    analysis = analyze_plan(plan, db)
    cycle_days = analysis["analysisMetadata"]["nativePeriodDays"]
    period_days = int(target_profile["periodDays"])
    scale = period_days / cycle_days
    effective = analysis["nativeCycle"]["effectiveSets"]
    results: dict[str, Any] = {}
    for muscle, target in sorted(target_profile.get("muscles", {}).items()):
        minimum, desired, maximum = _range(target)
        actual = round(float(effective.get(muscle, 0.0)) * scale, 6)
        if minimum is not None and actual < minimum:
            state = "below_minimum"
        elif maximum is not None and actual > maximum:
            state = "above_maximum"
        else:
            state = "within_range"
        results[muscle] = {
            "actualEffectiveSets": actual,
            "min": minimum, "target": desired, "max": maximum,
            "state": state,
            "periodDays": period_days,
        }
    return {
        "analysisVersion": "0.1.0",
        "plan": analysis["plan"],
        "target": {"targetId": target_profile.get("targetId"), "periodDays": period_days},
        "analysisMetadata": {**analysis["analysisMetadata"], "comparisonPeriodDays": period_days},
        "coverageCompleteness": analysis["coverageCompleteness"],
        "muscles": results,
    }

__all__ = ["compare_to_targets", "validate_target"]
