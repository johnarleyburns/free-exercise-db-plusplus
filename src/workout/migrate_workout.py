"""Deterministic forward migration from workout schema 0.1 to 0.2."""
from copy import deepcopy

def migrate(workout: dict) -> dict:
    result = deepcopy(workout)
    version = result.get("schemaVersion")
    if version == "0.2.0":
        return result
    if not isinstance(version, str) or not version.startswith("0.1."):
        raise ValueError(f"unsupported workout schema: {version!r}")
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
