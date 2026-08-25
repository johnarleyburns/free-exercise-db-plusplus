"""Shared, explicit policies and numeric range helpers for analysis."""
from __future__ import annotations
from typing import Any, Iterable
ANALYSIS_VERSION = "1.0.0"
ANALYSIS_POLICY = "dbpp-default-volume-v1"
RANGE_POLICY = "target-then-min-then-max"
UNIT_POLICY = "dbpp-conservative-units-v1"
COUNTED_SET_TYPES = frozenset({"working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"})
EXCLUDED_SET_TYPES = frozenset({"warmup", "technique", "test", "isometric", "other"})

def normalize_range(value: Any) -> dict[str, float]:
    if isinstance(value, (int, float)):
        number = float(value); return {"min": number, "target": number, "max": number}
    if not isinstance(value, dict): return {"min": 0.0, "target": 0.0, "max": 0.0}
    target = value.get("target")
    minimum = value.get("min", target if target is not None else value.get("max", 0.0))
    maximum = value.get("max", target if target is not None else minimum)
    if target is None: target = minimum if minimum is not None else maximum
    return {"min": float(minimum), "target": float(target), "max": float(maximum)}

def add_ranges(a: Any, b: Any) -> dict[str, float]:
    left, right = normalize_range(a), normalize_range(b)
    return {key: left[key] + right[key] for key in ("min", "target", "max")}

def scale_range(value: Any, factor: float) -> dict[str, float]:
    value = normalize_range(value); return {key: value[key] * factor for key in ("min", "target", "max")}

def range_target(value: Any) -> float: return normalize_range(value)["target"]

def set_credits(db: Any) -> dict[str, float]:
    metadata = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
    credits = metadata.get("setCredits") or {}
    # Legacy synthetic/consumer DBs predate metadata.setCredits; retain the shipped values only as a compatibility fallback.
    defaults = {"direct": 1.0, "indirect": 0.5, "stabilizer": 0.0}
    return {role: float(credits.get(role, defaults[role])) for role in ("direct", "indirect", "stabilizer")}

def planned_set_range(prescription: dict[str, Any]) -> dict[str, float]:
    if "plannedSets" in prescription:
        return normalize_range(sum(1 for item in prescription["plannedSets"] if item.get("setType") in COUNTED_SET_TYPES))
    set_type = prescription.get("setType")
    if set_type is not None and set_type not in COUNTED_SET_TYPES:
        return normalize_range(0)
    return normalize_range(prescription.get("sets", 0))

def planned_set_count(prescription: dict[str, Any], *, range_policy: str = "target") -> float:
    values = planned_set_range(prescription); return values.get(range_policy, values["target"])

def set_is_counted(item: dict[str, Any]) -> bool:
    return item.get("completed") is True and (item.get("setType") is None or item.get("setType") in COUNTED_SET_TYPES)

def completed_exercise_sets(exercise: dict[str, Any], *, include_types: set[str] | None = None) -> list[dict[str, Any]]:
    if include_types is not None: return [item for item in exercise.get("sets", []) if item.get("completed") is True and item.get("setType") in include_types]
    return [item for item in exercise.get("sets", []) if set_is_counted(item)]

def completed_set_count(workout: dict[str, Any], *, include_types: set[str] | None = None) -> int:
    return sum(len(completed_exercise_sets(exercise, include_types=include_types)) for exercise in workout.get("exercises", []))

def sum_ranges(values: Iterable[Any]) -> dict[str, float]:
    total = normalize_range(0)
    for value in values: total = add_ranges(total, value)
    return total

__all__ = ["ANALYSIS_POLICY", "ANALYSIS_VERSION", "COUNTED_SET_TYPES", "EXCLUDED_SET_TYPES", "RANGE_POLICY", "UNIT_POLICY", "add_ranges", "completed_exercise_sets", "completed_set_count", "normalize_range", "planned_set_count", "planned_set_range", "range_target", "scale_range", "set_credits", "set_is_counted", "sum_ranges"]
