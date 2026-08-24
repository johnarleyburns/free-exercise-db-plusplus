from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterator

@dataclass(frozen=True)
class Exercise:
    exercise_id: str
    data: dict[str, Any]

    @property
    def annotation(self) -> dict[str, Any]:
        return self.data.get("annotation", {})

    @property
    def volume_eligible(self) -> bool:
        return bool(self.annotation.get("volumeEligible", False))

class Database:
    """Read-only access to a Free Exercise DB++ JSON document."""
    def __init__(self, document: dict[str, Any]):
        if not isinstance(document.get("exercises"), dict):
            raise ValueError("database document must contain an exercises object")
        self._document = document
        self._exercises = {key: Exercise(key, value) for key, value in document["exercises"].items()}

    @classmethod
    def load(cls, path: str | Path) -> "Database":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def metadata(self) -> dict[str, Any]:
        return self._document.get("metadata", {})

    def get_exercise(self, exercise_id: str) -> Exercise:
        try:
            return self._exercises[exercise_id]
        except KeyError as exc:
            raise KeyError(f"unknown exerciseId: {exercise_id}") from exc

    def find_exercises(self, query: str) -> list[Exercise]:
        needle = query.casefold()
        return [e for e in self._exercises.values() if needle in e.exercise_id.casefold() or needle in str(e.data.get("name", "")).casefold()]

    def exercises_for_muscle(self, muscle: str, role: str | None = None) -> list[Exercise]:
        if role is not None and role not in {"direct", "indirect", "stabilizers"}:
            raise ValueError("role must be direct, indirect, or stabilizers")
        result=[]
        for exercise in self._exercises.values():
            ann=exercise.annotation
            roles=[role] if role else ["direct", "indirect", "stabilizers"]
            if any(muscle in ann.get(r, []) for r in roles): result.append(exercise)
        return result

    def __len__(self) -> int: return len(self._exercises)
    def __iter__(self) -> Iterator[Exercise]: return iter(self._exercises.values())
