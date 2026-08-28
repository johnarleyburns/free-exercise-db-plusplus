"""Stable application orchestration over the canonical DB++ engine.

This module deliberately contains dispatch and result shaping only.  The
training algorithms remain in their existing modules and the operation is
always explicit: a request for ``generate_plan`` can never silently become an
adaptation request.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

from .coaching import adapt_plan
from .intent import generate_plan_from_intent, resolve_intent
from .longitudinal import TrainingHistory
from .plan_evaluation import evaluate_plan
from .planning import generate_plan
from .progression import suggest_progression
from .training_state import derive_training_state

APPLICATION_SCHEMA_VERSION = "0.1.0"
OPERATIONS = frozenset({
    "resolve_intent", "generate_from_intent", "generate_plan", "evaluate_plan",
    "derive_state", "suggest_progression", "adapt_plan",
})


@dataclass(frozen=True)
class TrainingRequest:
    """Transport-neutral request accepted by :func:`process_training_request`."""

    operation: str
    request_id: str
    schema_version: str = APPLICATION_SCHEMA_VERSION
    intent: Any = None
    profile: Any = None
    target: Any = None
    history: Any = None
    training_state: Any = None
    current_plan: Any = None
    plan: Any = None
    as_of: str | None = None
    history_window: Any = None
    options: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "TrainingRequest":
        if not isinstance(document, Mapping):
            raise TypeError("training request must be an object")
        return cls(
            operation=str(document.get("operation", "")),
            request_id=str(document.get("requestId", "")),
            schema_version=str(document.get("schemaVersion", APPLICATION_SCHEMA_VERSION)),
            intent=document.get("intent"), profile=document.get("profile"),
            target=document.get("target"), history=document.get("history"),
            training_state=document.get("trainingState"),
            current_plan=document.get("currentPlan"), plan=document.get("plan"),
            as_of=document.get("asOf"), history_window=document.get("historyWindow"),
            options=dict(document.get("options") or {}),
        )

    @classmethod
    def load(cls, path: str | Path) -> "TrainingRequest":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        values = {
            "schemaVersion": self.schema_version, "requestId": self.request_id,
            "operation": self.operation, "intent": self.intent,
            "profile": self.profile, "target": self.target, "history": self.history,
            "trainingState": self.training_state, "currentPlan": self.current_plan,
            "plan": self.plan, "asOf": self.as_of,
            "historyWindow": self.history_window, "options": dict(self.options),
        }
        return {key: value for key, value in values.items() if value is not None}


class TrainingResult(dict):
    """Dictionary-compatible application result with convenient attributes."""

    @property
    def status(self) -> str:
        return self["status"]

    @property
    def operation(self) -> str:
        return self["operation"]

    @property
    def plan(self) -> Any:
        return self.get("plan")

    @property
    def resolution(self) -> Any:
        return self.get("resolution")

    @property
    def training_state(self) -> Any:
        return self.get("trainingState")

    @property
    def coach_decisions(self) -> list[Any]:
        return self.get("coachDecisions", [])

    def to_dict(self) -> dict[str, Any]:
        return dict(self)


def _history(value: Any) -> TrainingHistory:
    if isinstance(value, TrainingHistory):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("history is required and must be a TrainingHistory or object")
    return TrainingHistory(
        str(value["subjectId"]), value.get("plans", []), value.get("workouts", []),
        value.get("targets", []), value.get("planActivations", []), value.get("metadata", {}),
    )


def _request(value: TrainingRequest | Mapping[str, Any]) -> TrainingRequest:
    return value if isinstance(value, TrainingRequest) else TrainingRequest.from_dict(value)


def _envelope(request: TrainingRequest, status: str, *, resolution: Any = None,
              plan: Any = None, evaluation: Any = None, training_state: Any = None,
              coach_decisions: list[Any] | None = None, adaptation: Any = None,
              missing: list[Any] | None = None, conflicts: list[Any] | None = None,
              warnings: list[Any] | None = None, issues: list[Any] | None = None,
              provenance: Mapping[str, Any] | None = None) -> TrainingResult:
    return TrainingResult({
        "schemaVersion": APPLICATION_SCHEMA_VERSION,
        "requestId": request.request_id,
        "operation": request.operation,
        "status": status,
        "resolution": resolution,
        "plan": plan,
        "evaluation": evaluation,
        "trainingState": training_state,
        "coachDecisions": coach_decisions or [],
        "adaptation": adaptation,
        "missingInformation": missing or [],
        "conflicts": conflicts or [],
        "warnings": warnings or [],
        "issues": issues or [],
        "provenance": dict(provenance or {}),
    })


def process_training_request(request: TrainingRequest | Mapping[str, Any], db: Any,
                             relationships: Any = None) -> TrainingResult:
    """Dispatch one explicit application operation through canonical APIs.

    Normal domain outcomes are returned in the result envelope.  Missing
    operation inputs are represented as ``invalid`` rather than guessed or
    filled using the current clock.
    """
    req = _request(request)
    if req.schema_version != APPLICATION_SCHEMA_VERSION or not req.request_id or req.operation not in OPERATIONS:
        return _envelope(req, "invalid", issues=[{"code": "INVALID_REQUEST"}],
                         provenance={"requestSchemaVersion": req.schema_version})

    if req.operation == "resolve_intent":
        if req.intent is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_INTENT"}])
        history = _history(req.history) if req.history is not None else None
        result = resolve_intent(req.intent, db, profile=req.profile, target=req.target,
                                relationships=relationships, history=history,
                                as_of=req.as_of)
        return _envelope(req, result["status"], resolution=result,
                         missing=result.get("missingInformation"),
                         conflicts=result.get("conflicts"), warnings=result.get("warnings"),
                         provenance=result.get("provenance"))

    if req.operation == "generate_from_intent":
        if req.intent is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_INTENT"}])
        result = generate_plan_from_intent(
            req.intent, db, profile=req.profile, target=req.target,
            relationships=relationships, history=_history(req.history) if req.history is not None else None, as_of=req.as_of,
            current_plan=req.current_plan,
        )
        resolution = result.get("resolution") or {}
        generation = result.get("generation") or {}
        if not generation:
            return _envelope(req, resolution.get("status", "invalid"), resolution=resolution,
                             missing=resolution.get("missingInformation"),
                             conflicts=resolution.get("conflicts"), warnings=resolution.get("warnings"),
                             provenance=resolution.get("provenance"))
        issues = (generation.get("unsatisfiedConstraints", []) +
                  generation.get("unsatisfiedTargets", []) +
                  generation.get("unsatisfiedSoftPreferences", []))
        return _envelope(req, generation["status"], resolution=resolution,
                         plan=generation.get("plan"), evaluation=generation.get("evaluation"),
                         issues=issues, warnings=resolution.get("warnings"),
                         provenance=generation.get("provenance"))

    if req.operation == "generate_plan":
        if req.profile is None or req.target is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_PROFILE_OR_TARGET"}])
        options = dict(req.options)
        result = generate_plan(
            req.profile, req.target, db, policy=options.pop("policy", "full-body-general-v1"),
            training_state=req.training_state, relationships=relationships,
            current_plan=req.current_plan,
            requiredExerciseIds=options.pop("requiredExerciseIds", []),
            lockedExerciseIds=options.pop("lockedExerciseIds", []),
            requiredFamilyIds=options.pop("requiredFamilyIds", []),
            additionalExclusions=options.pop("additionalExclusions", []), options=options,
        )
        issues = (result.get("unsatisfiedConstraints", []) + result.get("unsatisfiedTargets", []) +
                  result.get("unsatisfiedSoftPreferences", []))
        return _envelope(req, result["status"], plan=result.get("plan"),
                         evaluation=result.get("evaluation"), issues=issues,
                         provenance=result.get("provenance"))

    if req.operation == "evaluate_plan":
        if req.plan is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_PLAN"}])
        result = evaluate_plan(req.plan, db, req.profile, req.target, relationships)
        return _envelope(req, "evaluated", plan=req.plan, evaluation=result,
                         warnings=result.get("warnings"),
                         issues=result.get("constraints", {}).get("violations", []),
                         provenance=result.get("provenance"))

    if req.operation == "derive_state":
        if req.history is None or req.as_of is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_HISTORY_OR_AS_OF"}])
        state = derive_training_state(
            _history(req.history), db, as_of=req.as_of,
            window=req.history_window or "last_28_days", relationships=relationships,
            target=req.target, timezone=dict(req.options).get("timezone", "UTC"),
        )
        return _envelope(req, "state_derived", training_state=state,
                         provenance=state.get("provenance"))

    if req.operation == "suggest_progression":
        if req.plan is None or req.training_state is None:
            return _envelope(req, "invalid", issues=[{"code": "MISSING_PLAN_OR_TRAINING_STATE"}])
        options = dict(req.options)
        decisions = suggest_progression(
            req.plan, req.training_state,
            policy=options.pop("policy", "double-progression-v1"), parameters=options or None,
        )
        return _envelope(req, "progression_available" if decisions else "insufficient_data",
                         plan=req.plan, coach_decisions=decisions)

    if req.operation == "adapt_plan":
        if any(value is None for value in (req.current_plan, req.profile, req.target, req.history, req.as_of)):
            return _envelope(req, "invalid", issues=[{"code": "MISSING_ADAPTATION_INPUT"}])
        options = dict(req.options)
        options.setdefault("asOf", req.as_of)
        result = adapt_plan(
            req.profile, req.target, req.current_plan, _history(req.history), db,
            policy=options.pop("policy", "general-adaptive-v1"), relationships=relationships,
            training_state=req.training_state, planning_policy=options.pop("planningPolicy", None),
            options=options,
        )
        return _envelope(req, result["status"], plan=result.get("currentPlan"),
                         training_state=result.get("trainingState"),
                         coach_decisions=result.get("decisions", []), adaptation=result,
                         issues=result.get("unresolvedIssues", []),
                         provenance=result.get("provenance"))

    return _envelope(req, "invalid", issues=[{"code": "UNSUPPORTED_OPERATION"}])


__all__ = ["APPLICATION_SCHEMA_VERSION", "OPERATIONS", "TrainingRequest", "TrainingResult", "process_training_request"]
