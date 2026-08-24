"""Deterministic forward migration for Workout PLAN documents."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

def migrate_to_02(plan: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(plan)
    version = result.get("schemaVersion")
    if version == "0.2.0": return result
    if version != "0.1.0": raise ValueError(f"unsupported PLAN schema for 0.2 migration: {version!r}")
    result["schemaVersion"] = "0.2.0"
    return result

def migrate(plan: dict[str, Any], target_version: str = "0.2.0") -> dict[str, Any]:
    if target_version == "0.2.0": return migrate_to_02(plan)
    if target_version == "0.1.0" and plan.get("schemaVersion") == "0.1.0": return deepcopy(plan)
    raise ValueError(f"unsupported target PLAN schema: {target_version!r}")
