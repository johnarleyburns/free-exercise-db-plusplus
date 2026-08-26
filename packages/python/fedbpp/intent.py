"""v1.10 structured WorkoutIntent resolution; deliberately no language-model integration.

This module is a resolution boundary, not a planner: it turns an already
structured request into the stable v1.6--v1.9 planning inputs.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .planning import PLANNING_POLICIES, generate_plan
from .training import validate_training_profile
from .training_state import derive_training_state
from .plan_evaluation import evaluate_plan
from ._analysis.targets import validate_target

INTENT_SCHEMA_VERSION = "0.1.0"
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
ENVIRONMENT_POLICIES = {
    "commercial-gym-general-v1": {"policyId": "commercial-gym-general-v1", "policyVersion": "1", "environment": "commercial_gym", "equipment": ("bands", "barbell", "body only", "cable", "dumbbell", "e-z curl bar", "exercise ball", "kettlebells", "machine", "medicine ball"), "description": "Common commercial-gym convenience default; it does not guarantee local availability."},
    "bodyweight-only-v1": {"policyId": "bodyweight-only-v1", "policyVersion": "1", "environment": "bodyweight_only", "equipment": ("body only",), "description": "Exercises requiring no external equipment."},
    "minimal-equipment-general-v1": {"policyId": "minimal-equipment-general-v1", "policyVersion": "1", "environment": "minimal_equipment", "equipment": ("bands", "body only", "dumbbell"), "description": "Conservative minimal-equipment convenience default."},
}
GOAL_POLICIES = {
    "general-hypertrophy-v1": {"goal": "hypertrophy", "policyVersion": "1", "planningPolicy": "full-body-general-v1", "reps": {"min": 6, "target": 8, "max": 12}, "effort": {"rir": 2}, "muscles": {"chest": {"target": 6}, "lats": {"target": 6}, "quadriceps": {"target": 6}, "hamstrings": {"target": 4}}, "description": "General, conservative coverage defaults; not an optimal prescription."},
    "general-strength-v1": {"goal": "strength", "policyVersion": "1", "planningPolicy": "full-body-general-v1", "reps": {"min": 3, "target": 5, "max": 6}, "effort": {"rir": 2}, "muscles": {"chest": {"target": 3}, "quadriceps": {"target": 3}, "hamstrings": {"target": 2}}, "description": "Minimal generic strength defaults; exercise-specific strength programming remains out of scope."},
}


class WorkoutIntent:
    """Portable WorkoutIntent 0.1 document with optional DB-aware validation."""
    def __init__(self, document: dict[str, Any]): self.document = document

    @classmethod
    def from_dict(cls, document: dict[str, Any], *, validate: bool = True, db: Any = None, relationships: Any = None) -> "WorkoutIntent":
        result = cls(document)
        if validate: result.validate(db, relationships)
        return result

    @classmethod
    def load(cls, path: str | Path, *, validate: bool = True, db: Any = None, relationships: Any = None) -> "WorkoutIntent":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")), validate=validate, db=db, relationships=relationships)

    def validate(self, db: Any = None, relationships: Any = None) -> None:
        errors = validate_workout_intent(self.document, db, relationships)
        if errors: raise ValueError("; ".join(errors))

def _doc(value: Any) -> dict[str, Any]: return value.document if hasattr(value, "document") else (value.data if hasattr(value, "data") else value)
def _known(db: Any) -> set[str]: return set(db._exercises) if hasattr(db, "_exercises") else set((db or {}).get("exercises", {}))
def _families(relationships: Any) -> set[str]: return set(relationships._families) if hasattr(relationships, "_families") else set((relationships or {}).get("families", {}))
def _equipment(db: Any) -> set[str]:
    if db is None: return set()
    return {str((_doc(db.get_exercise(eid)) if hasattr(db, "get_exercise") else (db.get("exercises", {}).get(eid) or {})).get("source", {}).get("equipment")) for eid in _known(db)}

def _schema_errors(intent: Any) -> list[str]:
    """Use the shipped schema when jsonschema is available, as other artifacts do."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return []
    schema = json.loads((Path(__file__).with_name("schemas") / "workout-intent.schema.json").read_text(encoding="utf-8"))
    return [f"{'.'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}" for error in Draft202012Validator(schema).iter_errors(intent)]
def _range_errors(value: Any, field: str) -> list[str]:
    if not isinstance(value, dict): return []
    lo, target, hi = value.get("min"), value.get("target"), value.get("max")
    return ([f"{field}: min must not exceed max"] if lo is not None and hi is not None and lo > hi else []) + ([f"{field}: target must not be below min"] if lo is not None and target is not None and target < lo else []) + ([f"{field}: target must not exceed max"] if hi is not None and target is not None and target > hi else [])

def validate_workout_intent(intent: dict[str, Any], db: Any = None, relationships: Any = None) -> list[str]:
    if not isinstance(intent, dict): return ["<root>: must be an object"]
    allowed = {"schemaVersion", "intentId", "subjectId", "goal", "schedule", "sessionConstraints", "environment", "equipmentOverrides", "exerciseConstraints", "preferences", "continuity", "useHistory", "historyWindow", "requestedPlanningPolicy", "requestedGoalPolicy"}
    errors = _schema_errors(intent) + [f"<root>: additional property {key}" for key in intent if key not in allowed]
    if intent.get("schemaVersion") != INTENT_SCHEMA_VERSION: errors.append("schemaVersion: must be 0.1.0")
    schedule = intent.get("schedule", {}) or {}; errors += _range_errors(schedule.get("sessionsPerCycle"), "schedule.sessionsPerCycle")
    errors += _range_errors((intent.get("sessionConstraints", {}) or {}).get("exercisesPerSession"), "sessionConstraints.exercisesPerSession")
    cycle = schedule.get("cycleLengthDays")
    weekdays = set(schedule.get("preferredWeekdays", []) or []) | set(schedule.get("excludedWeekdays", []) or [])
    if weekdays and cycle != 7: errors.append("schedule weekday fields require cycleLengthDays of 7")
    if set(schedule.get("preferredWeekdays", []) or []) & set(schedule.get("excludedWeekdays", []) or []): errors.append("schedule: preferredWeekdays and excludedWeekdays conflict")
    if set(schedule.get("preferredDayOffsets", []) or []) & set(schedule.get("excludedDayOffsets", []) or []): errors.append("schedule: preferredDayOffsets and excludedDayOffsets conflict")
    if cycle and any(x < 0 or x >= cycle for x in set(schedule.get("preferredDayOffsets", []) or []) | set(schedule.get("excludedDayOffsets", []) or [])): errors.append("schedule day offsets must be within cycleLengthDays")
    constraints = intent.get("exerciseConstraints", {}) or {}; prefs = intent.get("preferences", {}) or {}
    if (set(constraints.get("requiredFamilyIds", []) or []) | set(constraints.get("excludedFamilyIds", []) or []) |
            set(prefs.get("preferredFamilyIds", []) or []) | set(prefs.get("avoidedFamilyIds", []) or [])) and relationships is None:
        errors.append("exercise family constraints require exercise relationships")
    for left, right in (("requiredExerciseIds", "excludedExerciseIds"), ("requiredFamilyIds", "excludedFamilyIds")):
        if set(constraints.get(left, []) or []) & set(constraints.get(right, []) or []): errors.append(f"exerciseConstraints: {left} conflicts with {right}")
    for left, right in (("preferredExerciseIds", "excludedExerciseIds"), ("avoidedExerciseIds", "excludedExerciseIds"), ("preferredFamilyIds", "excludedFamilyIds"), ("avoidedFamilyIds", "excludedFamilyIds")):
        if set(prefs.get(left, []) or []) & set(constraints.get(right, []) or []): errors.append(f"preferences: {left} conflicts with {right}")
    if intent.get("requestedGoalPolicy") and intent["requestedGoalPolicy"] not in GOAL_POLICIES: errors.append("requestedGoalPolicy: unknown goal policy")
    if intent.get("requestedPlanningPolicy") and intent["requestedPlanningPolicy"] not in PLANNING_POLICIES: errors.append("requestedPlanningPolicy: unknown planning policy")
    if db is not None:
        for key in ("requiredExerciseIds", "lockedExerciseIds", "excludedExerciseIds"):
            for value in constraints.get(key, []) or []:
                if value not in _known(db): errors.append(f"{key}: unknown exerciseId: {value}")
        for key in ("preferredExerciseIds", "avoidedExerciseIds"):
            for value in prefs.get(key, []) or []:
                if value not in _known(db): errors.append(f"{key}: unknown exerciseId: {value}")
        for key in ("addEquipment", "removeEquipment"):
            for value in (intent.get("equipmentOverrides", {}) or {}).get(key, []) or []:
                if value not in _equipment(db): errors.append(f"equipmentOverrides.{key}: unknown DB++ equipment value: {value}")
        if relationships is not None:
            for key in ("requiredFamilyIds", "excludedFamilyIds"):
                for value in constraints.get(key, []) or []:
                    if value not in _families(relationships): errors.append(f"{key}: unknown familyId: {value}")
            for key in ("preferredFamilyIds", "avoidedFamilyIds"):
                for value in prefs.get(key, []) or []:
                    if value not in _families(relationships): errors.append(f"{key}: unknown familyId: {value}")
    return sorted(set(errors))

def _merge_target(default: dict[str, Any], explicit: dict[str, Any] | None) -> dict[str, Any]:
    """Merge portable TARGETs field-by-field; range members never shallow-replace."""
    result = deepcopy(default)
    if not explicit: return result
    def section(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for name, value in override.items():
            merged[name] = {**deepcopy(merged.get(name, {})), **deepcopy(value)} if isinstance(value, dict) else deepcopy(value)
        return merged
    for key, value in explicit.items():
        if key == "muscles": result[key] = section(result.get(key, {}), value or {})
        elif key == "frequency" and isinstance(value, dict):
            result[key] = deepcopy(result.get(key, {})); result[key]["muscles"] = section(result[key].get("muscles", {}), value.get("muscles", {}))
        elif key in {"movementPatterns", "families"}: result[key] = section(result.get(key, {}), value or {})
        else: result[key] = deepcopy(value)
    return result

def resolve_intent(intent: Any, db: Any, profile: Any = None, target: Any = None, relationships: Any = None, history: Any = None, *, as_of: str | None = None) -> dict[str, Any]:
    supplied_profile = profile is not None
    intent = _doc(intent); profile = deepcopy(_doc(profile)) if supplied_profile else {}; target = _doc(target) if target is not None else None
    errors = validate_workout_intent(intent, db, relationships)
    missing = []
    if not intent.get("goal"): missing.append({"field": "goal", "reason": "required_for_goal_policy_resolution"})
    schedule = intent.get("schedule", {}) or {}
    if not schedule.get("cycleLengthDays"): missing.append({"field": "schedule.cycleLengthDays", "reason": "required_for_schedule_resolution"})
    if not schedule.get("sessionsPerCycle"): missing.append({"field": "schedule.sessionsPerCycle", "reason": "required_for_schedule_resolution"})
    if not intent.get("environment") and not profile.get("equipment"): missing.append({"field": "environmentOrEquipment", "reason": "required_for_equipment_resolution"})
    if intent.get("environment") == "home_gym" and not (profile.get("equipment") or (intent.get("equipmentOverrides", {}) or {}).get("addEquipment")):
        missing.append({"field": "equipmentOverrides.addEquipment", "reason": "home_gym_has_no_v1_preset"})
    if intent.get("environment") == "custom" and not ((intent.get("equipmentOverrides", {}) or {}).get("addEquipment") or profile.get("equipment")): missing.append({"field": "equipmentOverrides.addEquipment", "reason": "required_for_custom_environment"})
    if errors: return {"status": "invalid", "resolvedProfile": None, "resolvedTarget": None, "planningPolicy": None, "goalPolicy": None, "environmentPolicy": None, "generationOptions": {}, "missingInformation": [], "warnings": [], "conflicts": [{"code": "INVALID_INTENT", "detail": x} for x in errors], "defaultsApplied": [], "provenance": {"intentSchemaVersion": intent.get("schemaVersion")}}
    if missing: return {"status": "needs_clarification", "resolvedProfile": None, "resolvedTarget": None, "planningPolicy": None, "goalPolicy": None, "environmentPolicy": None, "generationOptions": {}, "missingInformation": missing, "warnings": [], "conflicts": [], "defaultsApplied": [], "provenance": {"intentSchemaVersion": intent.get("schemaVersion")}}
    goal_policy_id = intent.get("requestedGoalPolicy") or {"hypertrophy": "general-hypertrophy-v1", "strength": "general-strength-v1"}.get(intent["goal"])
    if not goal_policy_id: return {"status": "needs_clarification", "resolvedProfile": None, "resolvedTarget": None, "planningPolicy": None, "goalPolicy": None, "environmentPolicy": None, "generationOptions": {}, "missingInformation": [{"field": "requestedGoalPolicy", "reason": "no_default_goal_policy_for_goal"}], "warnings": [], "conflicts": [], "defaultsApplied": [], "provenance": {"intentSchemaVersion": intent["schemaVersion"]}}
    gp = GOAL_POLICIES[goal_policy_id]; environment = intent.get("environment")
    if gp["goal"] != intent["goal"]:
        return {"status": "invalid", "resolvedProfile": None, "resolvedTarget": None, "planningPolicy": None, "goalPolicy": None, "environmentPolicy": None, "generationOptions": {}, "missingInformation": [], "warnings": [], "conflicts": [{"code": "GOAL_POLICY_MISMATCH", "goal": intent["goal"], "requestedGoalPolicy": goal_policy_id, "policyGoal": gp["goal"]}], "defaultsApplied": [], "explicitOverrides": [], "provenance": {"intentSchemaVersion": intent["schemaVersion"]}}
    env_id = next((key for key, value in ENVIRONMENT_POLICIES.items() if value["environment"] == environment), None)
    additions = set((intent.get("equipmentOverrides", {}) or {}).get("addEquipment", []) or []); removals = set((intent.get("equipmentOverrides", {}) or {}).get("removeEquipment", []) or [])
    if profile.get("equipment"):
        equipment = set(profile["equipment"]); env_id = None
    else: equipment = set(ENVIRONMENT_POLICIES.get(env_id, {}).get("equipment", ()))
    # A policy's canonical set is defined against the full DB++; restricting it
    # to a caller's deliberately partial DB fixture preserves DB-aware validity.
    if db is not None:
        known_equipment = _equipment(db)
        equipment = {value for value in equipment if value in known_equipment or value in {"bodyweight", "no equipment", "none"}}
    equipment = sorted((equipment | additions) - removals)
    constraints = intent.get("exerciseConstraints", {}) or {}; profile_constraints = profile.setdefault("constraints", {})
    conflicts = []
    excluded = set(profile_constraints.get("excludedExerciseIds", []) or []) | set(constraints.get("excludedExerciseIds", []) or [])
    required = set(constraints.get("requiredExerciseIds", []) or []) | set(constraints.get("lockedExerciseIds", []) or [])
    if required & excluded: conflicts += [{"code": "REQUIRED_EXERCISE_EXCLUDED", "exerciseId": x} for x in sorted(required & excluded)]
    excluded_families = set(profile_constraints.get("excludedFamilyIds", []) or []) | set(constraints.get("excludedFamilyIds", []) or [])
    required_families = set(constraints.get("requiredFamilyIds", []) or [])
    conflicts += [{"code": "REQUIRED_FAMILY_EXCLUDED", "familyId": x} for x in sorted(required_families & excluded_families)]
    profile_constraints["excludedExerciseIds"] = sorted(excluded)
    profile_constraints["excludedFamilyIds"] = sorted(excluded_families)
    profile.setdefault("schemaVersion", "0.1.0"); profile.setdefault("profileId", "resolved-profile"); profile["subjectId"] = intent.get("subjectId", profile.get("subjectId")); profile["goals"] = [{"type": intent["goal"]}]
    av = profile.setdefault("availability", {}); av.update({"cycleLengthDays": schedule["cycleLengthDays"], "sessionsPerCycle": deepcopy(schedule["sessionsPerCycle"]), "preferredDayOffsets": sorted(set(schedule.get("preferredDayOffsets", []) or []) | {WEEKDAYS.index(x) for x in schedule.get("preferredWeekdays", []) or []}), "excludedDayOffsets": sorted(set(schedule.get("excludedDayOffsets", []) or []) | {WEEKDAYS.index(x) for x in schedule.get("excludedWeekdays", []) or []})})
    if (intent.get("sessionConstraints", {}) or {}).get("exercisesPerSession") is not None: av["exercisesPerSession"] = deepcopy(intent["sessionConstraints"]["exercisesPerSession"])
    profile["equipment"] = equipment
    prefs = profile.setdefault("exercisePreferences", {}); prefs.update({key: sorted(set(prefs.get(key, []) or []) | set((intent.get("preferences", {}) or {}).get(key, []) or [])) for key in ("preferredExerciseIds", "avoidedExerciseIds", "preferredFamilyIds", "avoidedFamilyIds") if (intent.get("preferences", {}) or {}).get(key)})
    default_target = {"schemaVersion": "0.1.0", "targetId": f"{goal_policy_id}-default", "periodDays": schedule["cycleLengthDays"], "muscles": deepcopy(gp["muscles"]), "notes": gp["description"]}
    resolved_target = _merge_target(default_target, target)
    target_errors = validate_target(resolved_target)
    if target_errors:
        return {"status": "invalid", "resolvedProfile": None, "resolvedTarget": resolved_target, "planningPolicy": None, "goalPolicy": None, "environmentPolicy": None, "generationOptions": {}, "missingInformation": [], "warnings": [], "conflicts": [{"code": "TARGET_OVERRIDE_CONFLICT", "detail": error} for error in target_errors], "defaultsApplied": [], "explicitOverrides": [], "provenance": {"intentSchemaVersion": intent["schemaVersion"]}}
    policy_id = intent.get("requestedPlanningPolicy") or gp["planningPolicy"]
    warnings = []; generation_options = {"continuity": intent.get("continuity", "neutral"), "repDefaults": gp["reps"], "effortDefaults": gp["effort"], "requiredFamilyIds": sorted(required_families)}
    if intent.get("useHistory"):
        if history is None: warnings.append("useHistory was requested but no history was provided")
        elif as_of is None: warnings.append("useHistory was requested but as_of is required to derive TrainingState")
        else: generation_options["trainingState"] = derive_training_state(history, db, as_of=as_of, window=intent.get("historyWindow", "last_28_days"), relationships=relationships, target=resolved_target)
    if conflicts or validate_training_profile(profile, db, relationships):
        conflicts += [{"code": "PROFILE_CONFLICT", "detail": x} for x in validate_training_profile(profile, db, relationships)]
        return {"status": "invalid", "resolvedProfile": profile, "resolvedTarget": resolved_target, "planningPolicy": policy_id, "goalPolicy": {"policyId": goal_policy_id, "policyVersion": gp["policyVersion"]}, "environmentPolicy": env_id, "generationOptions": generation_options, "missingInformation": [], "warnings": warnings, "conflicts": conflicts, "defaultsApplied": [], "provenance": {"intentSchemaVersion": intent["schemaVersion"]}}
    defaults = ([] if intent.get("requestedGoalPolicy") else ["goalPolicy"]) + ([] if intent.get("requestedPlanningPolicy") else ["planningPolicy"]) + (["environmentPolicy"] if env_id else [])
    explicit_overrides = sorted((["goalPolicy"] if intent.get("requestedGoalPolicy") else []) + (["planningPolicy"] if intent.get("requestedPlanningPolicy") else []) + (["target"] if target is not None else []) + (["trainingProfile"] if supplied_profile else []))
    if additions: explicit_overrides.append({"equipmentAdded": sorted(additions)})
    if removals: explicit_overrides.append({"equipmentRemoved": sorted(removals)})
    dbmd = db.metadata if hasattr(db, "metadata") else (db or {}).get("metadata", {})
    environment_provenance = {"policyId": env_id, "policyVersion": ENVIRONMENT_POLICIES[env_id]["policyVersion"]} if env_id else None
    return {"status": "resolved_with_defaults" if defaults else "resolved", "resolvedProfile": profile, "resolvedTarget": resolved_target, "planningPolicy": policy_id, "goalPolicy": {"policyId": goal_policy_id, "policyVersion": gp["policyVersion"], "description": gp["description"]}, "environmentPolicy": env_id, "generationOptions": generation_options, "missingInformation": [], "warnings": warnings, "conflicts": [], "defaultsApplied": defaults, "explicitOverrides": explicit_overrides, "provenance": {"intentSchemaVersion": intent["schemaVersion"], "goalPolicy": {"policyId": goal_policy_id, "policyVersion": gp["policyVersion"]}, "environmentPolicy": environment_provenance, "dbSchemaVersion": dbmd.get("schemaVersion"), "dbConverterVersion": dbmd.get("converterVersion"), "relationshipSchemaVersion": relationships.document.get("schemaVersion") if hasattr(relationships, "document") else (relationships or {}).get("schemaVersion") if relationships else None}}

def generate_plan_from_intent(intent: Any, db: Any, profile: Any = None, target: Any = None, relationships: Any = None, history: Any = None, *, as_of: str | None = None, current_plan: Any = None) -> dict[str, Any]:
    resolution = resolve_intent(intent, db, profile, target, relationships, history, as_of=as_of)
    if resolution["status"] not in {"resolved", "resolved_with_defaults"}: return {"resolution": resolution, "generation": None}
    options = dict(resolution["generationOptions"]); state = options.pop("trainingState", None)
    generation = generate_plan(resolution["resolvedProfile"], resolution["resolvedTarget"], db, policy=resolution["planningPolicy"], relationships=relationships, training_state=state, current_plan=current_plan, requiredExerciseIds=(intent.get("exerciseConstraints", {}) or {}).get("requiredExerciseIds"), lockedExerciseIds=(intent.get("exerciseConstraints", {}) or {}).get("lockedExerciseIds"), requiredFamilyIds=options.pop("requiredFamilyIds", ()), options=options)
    if generation["plan"] is not None: generation["evaluation"] = evaluate_plan(generation["plan"], db, resolution["resolvedProfile"], resolution["resolvedTarget"], relationships)
    return {"resolution": resolution, "generation": generation}

__all__ = ["WorkoutIntent", "ENVIRONMENT_POLICIES", "GOAL_POLICIES", "validate_workout_intent", "resolve_intent", "generate_plan_from_intent"]
