from collections import defaultdict
import json
from pathlib import Path
from typing import Any

class ValidationError(ValueError): pass

class Workout:
    """Workout 0.2 document with optional JSON Schema validation."""
    def __init__(self, document: dict[str, Any]): self.document=document

    @classmethod
    def load(cls, path: str | Path, *, validate: bool = True, schema_path: str | Path | None = None) -> "Workout":
        document=json.loads(Path(path).read_text(encoding="utf-8")); result=cls(document)
        if validate: result.validate(schema_path=schema_path)
        return result

    @classmethod
    def from_dict(cls, document: dict[str, Any], *, validate: bool = True, schema_path: str | Path | None = None) -> "Workout":
        result=cls(document)
        if validate: result.validate(schema_path=schema_path)
        return result

    def validate(self, *, schema_path: str | Path | None = None) -> None:
        try:
            import jsonschema
        except ImportError as exc: raise ValidationError("validation requires the jsonschema package") from exc
        schema_file=Path(schema_path) if schema_path else Path(__file__).resolve().parents[3] / "workout.schema.json"
        schema=json.loads(schema_file.read_text(encoding="utf-8"))
        errors=sorted(jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(self.document), key=lambda e: list(e.path))
        if errors: raise ValidationError("; ".join(e.message for e in errors))

    def effective_sets(self, database: Any) -> dict[str, float]:
        """Return effective-set totals by muscle using DB++'s 1.0/0.5/0.0 credits."""
        totals=defaultdict(float)
        for observation in self.document.get("exercises", []):
            exercise_id=observation.get("exerciseId")
            if not exercise_id: continue
            exercise=database.get_exercise(exercise_id)
            if not exercise.volume_eligible: continue
            sets=sum(1 for item in observation.get("sets", []) if item.get("completed") is True)
            ann=exercise.annotation
            for muscle in ann.get("direct", []): totals[muscle] += sets * 1.0
            for muscle in ann.get("indirect", []): totals[muscle] += sets * 0.5
        return dict(sorted(totals.items()))

    def migrate(self) -> "Workout":
        from src.workout.migrate_workout import migrate
        return Workout(migrate(self.document))
