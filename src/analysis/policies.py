"""Explicit counted-set policies for PLAN and ACTUAL analysis."""
from __future__ import annotations

from typing import Any


def planned_set_count(prescription: dict[str, Any], *, range_policy: str = "target") -> float:
    """Resolve an exact/ranged PLAN prescription to an analysis count."""
    if "plannedSets" in prescription:
        return float(len(prescription["plannedSets"]))
    value = prescription.get("sets", 0)
    if isinstance(value, dict):
        for key in (range_policy, "target", "min", "max"):
            if key in value:
                return float(value[key])
        return 0.0
    return float(value)


def completed_set_count(workout: dict[str, Any], *, include_types: set[str] | None = None) -> int:
    """Count completed ACTUAL sets, optionally restricted by set type."""
    return sum(
        1 for exercise in workout.get("exercises", [])
        for item in exercise.get("sets", [])
        if item.get("completed", False)
        and (include_types is None or item.get("setType") in include_types)
    )


__all__ = ["completed_set_count", "planned_set_count"]
