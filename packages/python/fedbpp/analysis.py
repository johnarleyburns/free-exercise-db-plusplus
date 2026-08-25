"""Public access to the reference PLAN/TARGET/ACTUAL analyses."""
from __future__ import annotations

from typing import Any

from src.analysis import analyze_plan, analyze_plan_actual, compare_plans, compare_to_targets


def _document(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


def analyze(plan: Any, database: Any) -> dict[str, Any]:
    return analyze_plan(_document(plan), _document(database))


def compare_plan_actual(plan: Any, actual: Any, database: Any) -> dict[str, Any]:
    return analyze_plan_actual(_document(plan), _document(actual), _document(database))


def compare_plan_revisions(plan_a: Any, plan_b: Any, database: Any) -> dict[str, Any]:
    return compare_plans(_document(plan_a), _document(plan_b), _document(database))


def compare_target(plan: Any, target: Any, database: Any) -> dict[str, Any]:
    return compare_to_targets(_document(plan), _document(target), _document(database))


__all__ = ["analyze", "compare_plan_actual", "compare_plan_revisions", "compare_target"]
