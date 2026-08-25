"""Python PLAN 0.1/0.2 consumer helpers."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .validation import validate_plan, PlanValidationError as ValidationError

class Plan:
    def __init__(self, document: dict[str, Any]): self.document=document
    @classmethod
    def load(cls, path: str | Path, *, validate: bool=True) -> "Plan":
        document=json.loads(Path(path).read_text(encoding="utf-8")); result=cls(document)
        if validate: result.validate()
        return result
    @classmethod
    def from_dict(cls, document: dict[str, Any], *, validate: bool=True) -> "Plan":
        result=cls(document)
        if validate: result.validate()
        return result
    def validate(self) -> None:
        errors=validate_plan(self.document)
        if errors: raise ValidationError("; ".join(errors))
    def coverage(self, database: Any) -> dict[str, Any]:
        from ._analysis.coverage import analyze_plan
        return analyze_plan(self.document, database)
    def compare(self, other: "Plan", database: Any) -> dict[str, Any]:
        from ._analysis.plan_compare import compare_plans
        return compare_plans(self.document, other.document, database)
    def compare_actual(self, workout: Any, database: Any) -> dict[str, Any]:
        from ._analysis.plan_actual import analyze_plan_actual
        document=workout.document if hasattr(workout, "document") else workout
        return analyze_plan_actual(self.document, document, database)
