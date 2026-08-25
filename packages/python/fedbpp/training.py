"""TrainingProfile schema and DB-aware semantic validation."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).with_name("schemas")
GOALS = frozenset(("hypertrophy", "strength", "muscular_endurance", "general_fitness", "skill_practice", "power"))
EXPERIENCE = frozenset(("novice", "intermediate", "advanced", "unknown"))
PROFILE_KEYS = ("preferredExerciseIds", "avoidedExerciseIds", "preferredFamilyIds", "avoidedFamilyIds")

def _schema(path: str | Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or ROOT / "training-profile.schema.json").read_text(encoding="utf-8"))

def validate_training_profile(profile: dict[str, Any], db: Any = None, relationships: Any = None, *, schema_path: str | Path | None = None) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
        errors = [f"{'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in Draft202012Validator(_schema(schema_path)).iter_errors(profile)]
    except ImportError:
        errors = []
    if errors or not isinstance(profile, dict): return sorted(errors)
    errors = []
    goal_types = [goal.get("type") for goal in profile.get("goals", []) or []]
    if len(goal_types) != len(set(goal_types)): errors.append("goals: duplicate goal types are not allowed")
    availability = profile.get("availability", {}) or {}
    for field in ("sessionsPerCycle", "minutesPerSession"):
        value = availability.get(field)
        if value:
            if value.get("min") is not None and value.get("max") is not None and value["min"] > value["max"]: errors.append(f"availability.{field}: min must not exceed max")
            if value.get("target") is not None and value.get("min") is not None and value["target"] < value["min"]: errors.append(f"availability.{field}: target must not be below min")
            if value.get("target") is not None and value.get("max") is not None and value["target"] > value["max"]: errors.append(f"availability.{field}: target must not exceed max")
    offsets = set(availability.get("preferredDayOffsets", [])) | set(availability.get("excludedDayOffsets", []))
    cycle = availability.get("cycleLengthDays")
    if cycle and any(offset >= cycle for offset in offsets): errors.append("availability day offsets must be within cycleLengthDays")
    prefs = profile.get("exercisePreferences", {}) or {}
    constraints = profile.get("constraints", {}) or {}
    for left, right, label in (("preferredExerciseIds", "excludedExerciseIds", "exerciseId"), ("preferredFamilyIds", "excludedFamilyIds", "familyId"), ("avoidedExerciseIds", "excludedExerciseIds", "exerciseId"), ("avoidedFamilyIds", "excludedFamilyIds", "familyId"), ("preferredExerciseIds", "avoidedExerciseIds", "exerciseId"), ("preferredFamilyIds", "avoidedFamilyIds", "familyId")):
        overlap = sorted(set(prefs.get(left, [])) & set(constraints.get(right, [])))
        if overlap: errors.append(f"contradictory {label} preference/exclusion: {', '.join(overlap)}")
    if db is not None:
        known_exercises = set(db._exercises) if hasattr(db, "_exercises") else set((db.get("exercises") or {}).keys())
        for key in PROFILE_KEYS + ("excludedExerciseIds", "excludedFamilyIds"):
            if "ExerciseIds" in key:
                for value in (prefs.get(key, []) or []) + (constraints.get(key, []) or []):
                    if value not in known_exercises: errors.append(f"{key}: unknown exerciseId: {value}")
        if relationships is not None:
            known_families = set(relationships._families) if hasattr(relationships, "_families") else set((relationships.get("families") or {}).keys())
            for key in ("preferredFamilyIds", "avoidedFamilyIds"):
                for value in (prefs.get(key, []) or []):
                    if value not in known_families: errors.append(f"{key}: unknown familyId: {value}")
            for value in (constraints.get("excludedFamilyIds", []) or []):
                if value not in known_families: errors.append(f"excludedFamilyIds: unknown familyId: {value}")
        exercises = db if hasattr(db, "__iter__") and not isinstance(db, dict) else (db.get("exercises") or {}).values()
        known_equipment = {str((e.data if hasattr(e, "data") else e).get("source", {}).get("equipment")) for e in exercises}
        for value in profile.get("equipment", []) or []:
            if value not in known_equipment and value not in {"bodyweight", "no equipment", "none"}: errors.append(f"equipment: unknown DB++ equipment value: {value}")
    return sorted(set(errors))

class TrainingProfile:
    def __init__(self, document: dict[str, Any]): self.document = document
    @classmethod
    def load(cls, path: str | Path, *, validate: bool = True) -> "TrainingProfile":
        result = cls(json.loads(Path(path).read_text(encoding="utf-8")))
        if validate: result.validate()
        return result
    @classmethod
    def from_dict(cls, document: dict[str, Any], *, validate: bool = True) -> "TrainingProfile":
        result = cls(document)
        if validate: result.validate()
        return result
    def validate(self, db: Any = None, relationships: Any = None) -> None:
        errors = validate_training_profile(self.document, db, relationships)
        if errors: raise ValueError("; ".join(errors))

__all__ = ["TrainingProfile", "validate_training_profile"]
