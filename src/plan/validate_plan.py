"""Deterministic validation for Workout PLAN schema 0.1.0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "workout-plan.schema.json"


class PlanValidationError(ValueError):
    """Raised when a PLAN document fails schema or semantic validation."""


def _range_errors(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return []
    present = [value[key] for key in ("min", "target", "max") if key in value]
    errors: list[str] = []
    if "min" in value and "max" in value and value["min"] > value["max"]:
        errors.append(f"{path}: min must not exceed max")
    if "target" in value and "min" in value and value["target"] < value["min"]:
        errors.append(f"{path}: target must not be below min")
    if "target" in value and "max" in value and value["target"] > value["max"]:
        errors.append(f"{path}: target must not exceed max")
    if not present:
        errors.append(f"{path}: range needs min, target, or max")
    return errors


def semantic_errors(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sessions = plan.get("sessions", [])
    session_ids: set[str] = set()
    prescription_ids: set[str] = set()
    set_prescription_ids: set[str] = set()
    phase_ids = {phase.get("phaseId") for phase in plan.get("phases", [])}
    if plan.get("schemaVersion") == "0.1.0":
        forbidden_root = ("phases", "progression")
        for field in forbidden_root:
            if field in plan:
                errors.append(f"{field}: requires PLAN schemaVersion 0.2.0")
    if len(phase_ids) != len(plan.get("phases", [])):
        errors.append("phases.phaseId: duplicate ID")
    for si, session in enumerate(sessions):
        if session.get("phaseId") is not None and session.get("phaseId") not in phase_ids:
            errors.append(f"sessions[{si}].phaseId: unknown phase {session.get('phaseId')!r}")
        sid = session.get("planSessionId")
        if sid in session_ids:
            errors.append(f"sessions[{si}].planSessionId: duplicate ID {sid!r}")
        session_ids.add(sid)
        for ei, exercise in enumerate(session.get("exercises", [])):
            prefix = f"sessions[{si}].exercises[{ei}]"
            if plan.get("schemaVersion") == "0.1.0":
                for field in ("plannedSets", "progression", "optional", "condition"):
                    if field in exercise:
                        errors.append(f"{prefix}.{field}: requires PLAN schemaVersion 0.2.0")
            if "plannedSets" in exercise and any(field in exercise for field in ("sets", "reps", "load", "effort")):
                errors.append(f"{prefix}: aggregate sets/reps/load/effort and plannedSets are mutually exclusive")
            pid = exercise.get("prescriptionId")
            if pid in prescription_ids:
                errors.append(f"{prefix}.prescriptionId: duplicate ID {pid!r}")
            prescription_ids.add(pid)
            for field in ("sets", "reps"):
                errors.extend(_range_errors(exercise.get(field), f"{prefix}.{field}"))
            for set_index, planned_set in enumerate(exercise.get("plannedSets", [])):
                set_id = planned_set.get("setPrescriptionId")
                if set_id in set_prescription_ids:
                    errors.append(f"{prefix}.plannedSets[{set_index}].setPrescriptionId: duplicate ID {set_id!r}")
                set_prescription_ids.add(set_id)
                errors.extend(_range_errors(planned_set.get("reps"), f"{prefix}.plannedSets[{set_index}].reps"))
                planned_load = planned_set.get("load")
                if isinstance(planned_load, dict) and "unit" in planned_load and any(key in planned_load for key in ("min", "target", "max")):
                    errors.extend(_range_errors(planned_load, f"{prefix}.plannedSets[{set_index}].load"))
            load = exercise.get("load")
            if isinstance(load, dict) and "unit" in load and any(key in load for key in ("min", "target", "max")):
                errors.extend(_range_errors(load, f"{prefix}.load"))
            effort = exercise.get("effort") or {}
            if isinstance(effort, dict):
                for field in ("rpe", "rir"):
                    errors.extend(_range_errors(effort.get(field), f"{prefix}.effort.{field}"))
    return errors


def validate_plan(plan: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> list[str]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"{'.'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}" for error in validator.iter_errors(plan)]
    if not errors and isinstance(plan, dict):
        errors.extend(semantic_errors(plan))
    return sorted(errors)


def load_plan(path: str | Path) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_plan(plan)
    if errors:
        raise PlanValidationError("; ".join(errors))
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        load_plan(args.plan)
    except (OSError, json.JSONDecodeError, PlanValidationError) as exc:
        print(f"invalid PLAN: {exc}")
        return 1
    print(f"valid PLAN: {args.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
