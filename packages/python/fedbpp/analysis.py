"""Public access to the reference PLAN/TARGET/ACTUAL analyses."""
from __future__ import annotations

from typing import Any

from ._analysis.coverage import analyze_plan as _analyze_plan
from ._analysis.plan_actual import analyze_plan_actual
from ._analysis.plan_compare import compare_plans as _compare_plans
from ._analysis.targets import compare_to_targets as _compare_to_targets


def _document(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


def analyze_plan(plan: Any, database: Any, relationships: Any = None) -> dict[str, Any]:
    result = _analyze_plan(_document(plan), _document(database))
    if relationships is not None:
        from .relationships import family_coverage
        result["familyCoverage"] = family_coverage(_document(plan), relationships)
    return result


def compare_plan_actual(plan: Any, actual: Any, database: Any, relationships: Any = None) -> dict[str, Any]:
    result = analyze_plan_actual(_document(plan), _document(actual), _document(database))
    if relationships is not None:
        registry = relationships
        for row in result.get("matching", {}).get("exercises", []):
            planned_id, actual_id = row.get("plannedExerciseId"), row.get("actualExerciseId")
            if planned_id and actual_id:
                row["relationshipContext"] = registry.compare_dimensions(planned_id, actual_id)
                relation=registry.relationship(planned_id,actual_id)
                row["relationshipContext"]["relationship"] = relation.relationship if relation else None
                planned_family=registry.family_for(planned_id); actual_family=registry.family_for(actual_id)
                row["relationshipContext"]["plannedFamily"] = planned_family.family_id if planned_family else None
                row["relationshipContext"]["actualFamily"] = actual_family.family_id if actual_family else None
                if hasattr(registry, "compare_exercise_coverage"):
                    row["relationshipContext"]["coverageDifference"] = registry.compare_exercise_coverage(planned_id, actual_id, _document(database))["coverageDifference"]
    return result


def compare_plans(plan_a: Any, plan_b: Any, database: Any, relationships: Any = None) -> dict[str, Any]:
    result = _compare_plans(_document(plan_a), _document(plan_b), _document(database))
    if relationships is not None:
        from .relationships import family_coverage
        result["familyCoverage"] = {"planA": family_coverage(_document(plan_a), relationships), "planB": family_coverage(_document(plan_b), relationships)}
        a, b = result["familyCoverage"]["planA"], result["familyCoverage"]["planB"]
        differences={}
        for family_id in sorted(set(a)&set(b)):
            if a[family_id]["exerciseIds"]==b[family_id]["exerciseIds"]: continue
            pairs=[]
            for exercise_a in a[family_id]["exerciseIds"]:
                for exercise_b in b[family_id]["exerciseIds"]:
                    if exercise_a!=exercise_b: pairs.append({"exerciseA":exercise_a,"exerciseB":exercise_b,**relationships.compare_dimensions(exercise_a,exercise_b)})
            differences[family_id]={"planA":a[family_id]["exerciseIds"],"planB":b[family_id]["exerciseIds"],"sameFamily":True,"dimensionDifferences":pairs}
        result["familyComparison"] = {"onlyInA": sorted(set(a)-set(b)), "onlyInB": sorted(set(b)-set(a)), "inBoth": sorted(set(a)&set(b)), "variantDifferences": differences}
    return result


def compare_to_targets(plan: Any, target: Any, database: Any) -> dict[str, Any]:
    return _compare_to_targets(_document(plan), _document(target), _document(database))


# Backward-compatible 0.1 API aliases.
analyze = analyze_plan
compare_plan_revisions = compare_plans
compare_target = compare_to_targets

__all__ = ["analyze_plan", "compare_plan_actual", "compare_plans", "compare_to_targets"]
