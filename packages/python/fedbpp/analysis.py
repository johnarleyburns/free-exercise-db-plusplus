"""Public access to the reference PLAN/TARGET/ACTUAL analyses."""
from __future__ import annotations

from typing import Any

from ._analysis.coverage import analyze_plan as _analyze_plan
from ._analysis.plan_actual import analyze_plan_actual
from ._analysis.plan_compare import compare_plans as _compare_plans
from ._analysis.targets import compare_to_targets as _compare_to_targets


def _document(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


def analyze_plan(plan: Any, database: Any) -> dict[str, Any]:
    return _analyze_plan(_document(plan), _document(database))


def compare_plan_actual(plan: Any, actual: Any, database: Any) -> dict[str, Any]:
    return analyze_plan_actual(_document(plan), _document(actual), _document(database))


def compare_plans(plan_a: Any, plan_b: Any, database: Any) -> dict[str, Any]:
    return _compare_plans(_document(plan_a), _document(plan_b), _document(database))


def compare_to_targets(plan: Any, target: Any, database: Any) -> dict[str, Any]:
    return _compare_to_targets(_document(plan), _document(target), _document(database))


# Backward-compatible 0.1 API aliases.
analyze = analyze_plan
compare_plan_revisions = compare_plans
compare_target = compare_to_targets

__all__ = ["analyze_plan", "compare_plan_actual", "compare_plans", "compare_to_targets"]
