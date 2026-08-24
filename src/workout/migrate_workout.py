"""Deterministic forward migrations for Workout ACTUAL documents."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def migrate_to_02(workout: dict[str, Any]) -> dict[str, Any]:
    """Migrate a 0.1.x ACTUAL document to 0.2.0."""
    result = deepcopy(workout)
    version = result.get("schemaVersion")
    if version == "0.2.0":
        return result
    if not isinstance(version, str) or not version.startswith("0.1."):
        raise ValueError(f"unsupported workout schema for 0.2 migration: {version!r}")
    result["schemaVersion"] = "0.2.0"
    for exercise in result.get("exercises", []):
        exercise.setdefault("laterality", "unspecified")
        for item in exercise.get("sets", []):
            item.setdefault("laterality", None)
            if "repetitions" in item and item["repetitions"] is not None:
                for rep in item["repetitions"]:
                    if "velocity" in rep and "meanVelocity" not in rep:
                        rep["meanVelocity"] = rep.pop("velocity")
                    if "rangeOfMotion" in rep and isinstance(rep["rangeOfMotion"], (int, float)):
                        rep["rangeOfMotion"] = {"value": rep["rangeOfMotion"], "unit": "m"}
    return result


def migrate_to_03(workout: dict[str, Any]) -> dict[str, Any]:
    """Migrate ACTUAL 0.2.0 to 0.3.0 without inventing PLAN links."""
    result = deepcopy(workout)
    version = result.get("schemaVersion")
    if version == "0.3.0":
        return result
    if version != "0.2.0":
        raise ValueError(f"unsupported workout schema for 0.3 migration: {version!r}")
    result["schemaVersion"] = "0.3.0"
    return result


def migrate(workout: dict[str, Any], target_version: str = "0.3.0") -> dict[str, Any]:
    """Migrate forward to the requested ACTUAL version (0.2.0 or 0.3.0)."""
    if target_version == "0.2.0":
        return migrate_to_02(workout)
    if target_version == "0.3.0":
        version = workout.get("schemaVersion")
        if isinstance(version, str) and version.startswith("0.1."):
            return migrate_to_03(migrate_to_02(workout))
        return migrate_to_03(workout)
    raise ValueError(f"unsupported target workout schema: {target_version!r}")
