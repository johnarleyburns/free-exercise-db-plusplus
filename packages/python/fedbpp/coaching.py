"""Deterministic, advisory adaptive coaching.

This module is an orchestration boundary. It derives (or verifies) a
TrainingState, obtains CoachDecision facts from v1.7 progression, constructs
a copy of the supplied PLAN, and gates that copy through canonical validation
and evaluation. It never activates, stores, or mutates PLAN/ACTUAL history.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from ._analysis.policies import set_credits
from ._analysis.units import UnitError, normalize_quantity
from .longitudinal import TrainingHistory
from .plan import Plan
from .plan_evaluation import evaluate_plan
from .planning import generate_plan
from .progression import suggest_progression_for_plan
from .training import validate_training_profile
from .training_state import derive_training_state

COACHING_VERSION = "1.9.0"


@dataclass(frozen=True)
class CoachingPolicy:
    policyId: str
    policyVersion: str
    description: str
    stateWindowPolicy: str
    exerciseProgressionPolicy: str
    adherencePolicy: str
    volumeAdjustmentPolicy: str
    frequencyAdjustmentPolicy: str
    substitutionPolicy: str
    regenerationPolicy: str
    decisionPriority: tuple[str, ...]
    parameters: dict[str, Any]

    def document(self) -> dict[str, Any]:
        result = asdict(self)
        result["decisionPriority"] = list(self.decisionPriority)
        return result


COACHING_POLICIES = {
    "general-adaptive-v1": CoachingPolicy(
        "general-adaptive-v1", "1.0.0",
        "Conservative deterministic advisory adaptation. Ambiguous evidence holds the PLAN.",
        "last_28_days", "double-progression-v1", "quantitative-adherence-v1",
        "effective-set-one-step-v1", "canonical-exposure-v1", "explicit-substitution-v1",
        "v1.8-generator-v1",
        ("hard_constraints", "structural_invalidity", "target_minimums", "adherence",
         "repeated_failure", "progression", "target_optimization", "preferences",
         "continuity", "stable_tie_break"),
        {"minimumRecentPerformances": 2, "repeatedFailureThreshold": 2,
         "repeatedSkipThreshold": 2, "repeatedSubstitutionThreshold": 2,
         "maxSetsAddedPerMusclePerRevision": 1,
         "maxSetsRemovedPerMusclePerRevision": 1,
         "maxTotalSetChangesPerRevision": 2,
         "loadIncrement": {"value": 2.5, "unit": "kg"}},
    )
}


def _doc(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


def _exercise_data(db: Any, exercise_id: str) -> dict[str, Any] | None:
    try:
        item = db.get_exercise(exercise_id) if hasattr(db, "get_exercise") else db.get("exercises", {}).get(exercise_id)
    except KeyError:
        return None
    return item.data if hasattr(item, "data") else item


def _revision_id(current: Any, requested: str | None) -> str:
    current = str(current or "r1")
    if requested is not None:
        if requested == current:
            raise ValueError("proposed revisionId must differ from current revisionId")
        return requested
    return f"r{int(current[1:]) + 1}" if current.startswith("r") and current[1:].isdigit() else current + "-adaptive-1"


def _latest_timestamp(history: TrainingHistory) -> str | None:
    return max((str(w["startTime"]) for w in history.workouts if w.get("startTime")), default=None)


def _decision_id(prefix: str, prescription_id: Any = None) -> str:
    return f"decision-{prefix}" + (f"-{prescription_id}" if prescription_id else "")


def _normalize_decision(item: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(item)
    result["decisionId"] = _decision_id(result.get("decisionType", "hold"), result.get("prescriptionId"))
    result["reasonCodes"] = sorted(set(result.get("reasonCodes", [])))
    return result


def _change(kind: str, before: dict[str, Any], after: dict[str, Any], reasons: list[str], decision_id: str) -> dict[str, Any]:
    return {"type": kind, "prescriptionId": before.get("prescriptionId"), "exerciseId": before.get("exerciseId"),
            "before": deepcopy(before), "after": deepcopy(after), "reasonCodes": sorted(set(reasons)), "decisionIds": [decision_id]}


def _hard_invalid(evaluation: dict[str, Any]) -> bool:
    return not evaluation["summary"]["satisfiesHardConstraints"]


def _target_excess_count(evaluation: dict[str, Any]) -> int:
    sections = (evaluation.get("muscleCoverage", {}), evaluation.get("frequency", {}),
                evaluation.get("movementPatterns", {}), evaluation.get("families", {}).get("targets", {}))
    return sum(1 for section in sections for value in section.values() if value.get("state") == "above_maximum")


def _state_for_current(history: TrainingHistory, current: dict[str, Any]) -> TrainingHistory:
    """Supply current PLAN to canonical state derivation without changing history."""
    if any(p.get("planId") == current.get("planId") and p.get("revisionId") == current.get("revisionId") for p in history.plans):
        return history
    return TrainingHistory(history.subject_id, [*history.plans, deepcopy(current)], history.workouts,
                           history.targets, history.plan_activations, history.metadata)


def _regression(rx: dict[str, Any], state: dict[str, Any], policy: CoachingPolicy) -> dict[str, Any] | None:
    """Conservative repeated below-lower-bound regression; no units are guessed."""
    es = state.get("exerciseState", {}).get(rx.get("exerciseId"), {})
    performances = es.get("recentPerformances", [])
    reps = rx.get("reps"); lower = reps.get("min") if isinstance(reps, dict) else reps
    required = int(rx.get("sets", 0))
    if lower is None or not required or len(performances) < policy.parameters["repeatedFailureThreshold"]:
        return None
    failures = [p for p in performances if len(p.get("sets", [])) < required or any(
        s.get("reps") is None or float(s["reps"]) < float(lower) for s in p.get("sets", [])[:required])]
    if len(failures) < policy.parameters["repeatedFailureThreshold"]:
        return None
    load = rx.get("load") or {}
    try:
        unit = str(load["unit"]).lower()
        old = normalize_quantity({"value": load["value"], "unit": unit}, "kg")
        increment = normalize_quantity(policy.parameters["loadIncrement"], "kg")
        if old <= increment:
            raise ValueError
        after = {**load, "value": round(normalize_quantity({"value": old - increment, "unit": "kg"}, unit), 6)}
    except (KeyError, UnitError, ValueError, TypeError):
        return None
    return {"schemaVersion": "0.1.0", "decisionId": _decision_id("decrease_load", rx.get("prescriptionId")),
            "decisionType": "decrease_load", "policyId": policy.policyId, "policyVersion": policy.policyVersion,
            "planId": state.get("activePlan", {}).get("planId"), "revisionId": state.get("activePlan", {}).get("revisionId"),
            "prescriptionId": rx.get("prescriptionId"), "exerciseId": rx.get("exerciseId"),
            "before": {"load": deepcopy(load)}, "after": {"load": after},
            "reasonCodes": ["REPEATED_PERFORMANCE_FAILURE"],
            "evidence": {"performanceSessionIds": [p.get("sessionId") for p in failures]},
            "provenance": state.get("provenance", {})}


def _exercise_changes(candidate: dict[str, Any], state: dict[str, Any], policy: CoachingPolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    mapping = {rx.get("prescriptionId"): policy.exerciseProgressionPolicy for session in candidate.get("sessions", []) for rx in session.get("exercises", [])}
    for raw in suggest_progression_for_plan(candidate, state, policy_map=mapping, parameters={"loadIncrement": policy.parameters["loadIncrement"]}):
        decision = _normalize_decision(raw)
        es = state.get("exerciseState", {}).get(decision.get("exerciseId"), {})
        if decision["decisionType"] == "increase_load" and es.get("recentSessionCount", 0) < policy.parameters["minimumRecentPerformances"]:
            decision.update({"decisionId": _decision_id("insufficient_data", decision.get("prescriptionId")),
                             "decisionType": "insufficient_data", "after": deepcopy(decision["before"]),
                             "reasonCodes": ["INSUFFICIENT_HISTORY"]})
        decisions.append(decision)
        if decision["decisionType"] == "increase_load":
            for session in candidate.get("sessions", []):
                for rx in session.get("exercises", []):
                    if rx.get("prescriptionId") == decision.get("prescriptionId"):
                        before = deepcopy(rx); rx.update(deepcopy(decision["after"]))
                        changes.append(_change("LOAD_CHANGED", before, rx, ["PROGRESSION_CRITERIA_MET"], decision["decisionId"]))
    # Repeated failure wins over a same-prescription progression recommendation.
    for session in candidate.get("sessions", []):
        for rx in session.get("exercises", []):
            decision = _regression(rx, state, policy)
            if decision is None:
                continue
            rxid = rx.get("prescriptionId")
            decisions = [d for d in decisions if d.get("prescriptionId") != rxid or d.get("decisionType") != "increase_load"]
            changes = [c for c in changes if c.get("prescriptionId") != rxid]
            before = deepcopy(rx); rx.update(deepcopy(decision["after"]))
            decisions.append(decision)
            changes.append(_change("LOAD_CHANGED", before, rx, decision["reasonCodes"], decision["decisionId"]))
    return decisions, changes


def _volume_changes(candidate: dict[str, Any], evaluation: dict[str, Any], db: Any, policy: CoachingPolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    credits, budget = set_credits(db), policy.parameters["maxTotalSetChangesPerRevision"]
    rows = [rx for session in candidate.get("sessions", []) for rx in session.get("exercises", []) if isinstance(rx.get("sets"), int)]
    decisions: list[dict[str, Any]] = []; changes: list[dict[str, Any]] = []
    for muscle, coverage in sorted(evaluation.get("muscleCoverage", {}).items()):
        if budget <= 0 or coverage.get("state") not in {"below_minimum", "above_maximum"}:
            continue
        direction = 1 if coverage["state"] == "below_minimum" else -1
        ranked = []
        for rx in rows:
            ann = (_exercise_data(db, rx.get("exerciseId")) or {}).get("annotation", {})
            credit = sum(credits[role] for role, field in (("direct", "direct"), ("indirect", "indirect"), ("stabilizer", "stabilizers")) if muscle in ann.get(field, []))
            if credit and (direction > 0 or rx["sets"] > 1):
                ranked.append((-credit if direction > 0 else credit, rx.get("prescriptionId", ""), rx))
        if not ranked:
            continue
        rx = sorted(ranked)[0][2]; before = deepcopy(rx); rx["sets"] += direction
        typ, reason = ("increase_sets", "TARGET_VOLUME_DEFICIT") if direction > 0 else ("decrease_sets", "TARGET_VOLUME_EXCESS")
        did = _decision_id(typ, rx.get("prescriptionId"))
        decisions.append({"schemaVersion": "0.1.0", "decisionId": did, "decisionType": typ,
                          "policyId": policy.policyId, "policyVersion": policy.policyVersion,
                          "planId": candidate.get("planId"), "revisionId": candidate.get("revisionId"),
                          "prescriptionId": rx.get("prescriptionId"), "exerciseId": rx.get("exerciseId"),
                          "before": {"sets": before["sets"]}, "after": {"sets": rx["sets"]},
                          "reasonCodes": [reason], "evidence": {"muscleId": muscle, "effectiveSets": coverage.get("actualEffectiveSets")}, "provenance": {}})
        changes.append(_change("SETS_ADDED" if direction > 0 else "SETS_REMOVED", before, rx, [reason], did)); budget -= 1
    return decisions, changes


def _adherence_decisions(current: dict[str, Any], state: dict[str, Any], policy: CoachingPolicy) -> list[dict[str, Any]]:
    """Represent quantitative skips without pretending their cause is known."""
    skipped = state.get("adherenceState", {}).get("skippedPrescriptionCounts", {})
    result = []
    for session in current.get("sessions", []):
        for rx in session.get("exercises", []):
            count = int(skipped.get(rx.get("prescriptionId"), 0))
            if count < policy.parameters["repeatedSkipThreshold"]:
                continue
            result.append({"schemaVersion": "0.1.0", "decisionId": _decision_id("hold", rx.get("prescriptionId")),
                           "decisionType": "hold", "policyId": policy.policyId, "policyVersion": policy.policyVersion,
                           "planId": current.get("planId"), "revisionId": current.get("revisionId"),
                           "prescriptionId": rx.get("prescriptionId"), "exerciseId": rx.get("exerciseId"),
                           "before": {}, "after": {}, "reasonCodes": ["REPEATEDLY_SKIPPED"],
                           "evidence": {"skippedPrescriptionCount": count}, "provenance": state.get("provenance", {})})
    return result


def _allowed_replacement(exercise_id: str, profile: dict[str, Any], db: Any, relationships: Any) -> bool:
    data = _exercise_data(db, exercise_id)
    if data is None:
        return False
    constraints = profile.get("constraints", {}) or {}
    if exercise_id in set(constraints.get("excludedExerciseIds", []) or []):
        return False
    family = relationships.family_for(exercise_id).family_id if relationships and relationships.family_for(exercise_id) else None
    if family in set(constraints.get("excludedFamilyIds", []) or []):
        return False
    equipment = data.get("source", {}).get("equipment")
    available = set(profile.get("equipment", []) or [])
    return equipment in available or (equipment in {"body only", "bodyweight", "no equipment", "none"} and available & {"body only", "bodyweight", "no equipment", "none"})


def _substitution_changes(candidate: dict[str, Any], history: TrainingHistory | None, state: dict[str, Any], profile: dict[str, Any], db: Any, relationships: Any, policy: CoachingPolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Only explicit ACTUAL substitutions can propose an exercise replacement."""
    if history is None:
        return [], []
    observed: dict[str, dict[str, int]] = {}
    for workout in history.workouts:
        for actual in workout.get("exercises", []):
            substitution = actual.get("substitution") or {}
            rxid = actual.get("exercisePrescriptionId") or substitution.get("plannedPrescriptionId")
            replacement_id = actual.get("exerciseId")
            if rxid and replacement_id and substitution:
                observed.setdefault(rxid, {})[replacement_id] = observed.setdefault(rxid, {}).get(replacement_id, 0) + 1
    decisions: list[dict[str, Any]] = []; changes: list[dict[str, Any]] = []
    for session in candidate.get("sessions", []):
        for rx in session.get("exercises", []):
            rxid = rx.get("prescriptionId")
            choices = [(count, eid) for eid, count in observed.get(rxid, {}).items()
                       if eid != rx.get("exerciseId") and count >= policy.parameters["repeatedSubstitutionThreshold"] and _allowed_replacement(eid, profile, db, relationships)]
            if not choices:
                continue
            _, replacement = sorted(choices, key=lambda x: (-x[0], x[1]))[0]
            before = deepcopy(rx); rx["exerciseId"] = replacement
            source = _exercise_data(db, replacement) or {}
            if source.get("source", {}).get("name"):
                rx["exerciseName"] = source["source"]["name"]
            did = _decision_id("substitute_exercise", rxid)
            decisions.append({"schemaVersion": "0.1.0", "decisionId": did, "decisionType": "substitute_exercise",
                              "policyId": policy.policyId, "policyVersion": policy.policyVersion,
                              "planId": candidate.get("planId"), "revisionId": candidate.get("revisionId"),
                              "prescriptionId": rxid, "exerciseId": before.get("exerciseId"),
                              "before": {"exerciseId": before.get("exerciseId")}, "after": {"exerciseId": replacement},
                              "reasonCodes": ["REPEATED_SUBSTITUTION"],
                              "evidence": {"substitutionCount": observed[rxid][replacement], "replacementExerciseId": replacement},
                              "provenance": state.get("provenance", {})})
            changes.append(_change("EXERCISE_SUBSTITUTED", before, rx, ["REPEATED_SUBSTITUTION"], did))
    return decisions, changes


def _provenance(db: Any, state: dict[str, Any] | None, policy: CoachingPolicy, evaluation: dict[str, Any] | None, planning_policy: str | None) -> dict[str, Any]:
    md = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
    return {"coachingVersion": COACHING_VERSION, "coachingPolicyId": policy.policyId, "coachingPolicyVersion": policy.policyVersion,
            "planningPolicyId": planning_policy, "trainingStateVersion": (state or {}).get("stateVersion"),
            "historyWindow": (state or {}).get("historyWindow"), "stateProvenance": (state or {}).get("provenance"),
            "dbSchemaVersion": md.get("schemaVersion"), "dbConverterVersion": md.get("converterVersion"),
            "dbUpstreamSha256": (md.get("upstream") or {}).get("sha256"), "setCredits": set_credits(db),
            "evaluationVersion": (evaluation or {}).get("provenance", {}).get("analysisVersion")}


def _result(status: str, current: dict[str, Any], proposed: dict[str, Any] | None, current_eval: dict[str, Any] | None, proposed_eval: dict[str, Any] | None, state: dict[str, Any] | None, decisions: list[dict[str, Any]], changes: list[dict[str, Any]], unresolved: list[dict[str, Any]], db: Any, policy: CoachingPolicy, planning_policy: str | None) -> dict[str, Any]:
    return {"status": status, "currentPlan": deepcopy(current), "proposedPlan": deepcopy(proposed) if proposed else None,
            "currentEvaluation": current_eval, "proposedEvaluation": proposed_eval, "trainingState": state,
            "decisions": sorted(decisions, key=lambda x: (x.get("prescriptionId") or "", x.get("decisionType") or "", x.get("decisionId") or "")),
            "changes": sorted(changes, key=lambda x: (x.get("prescriptionId") or "", x["type"])),
            "unresolvedIssues": sorted(unresolved, key=lambda x: (x.get("code", ""), str(x))),
            "policy": policy.document(), "provenance": _provenance(db, state, policy, proposed_eval or current_eval, planning_policy)}


def adapt_plan(profile: Any, target: Any, current_plan: Any, history: TrainingHistory, db: Any, *, policy: str | CoachingPolicy = "general-adaptive-v1", relationships: Any = None, training_state: Any = None, planning_policy: str | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic proposal. The caller alone may activate or persist it."""
    profile, target, current, options = _doc(profile), _doc(target), _doc(current_plan), dict(options or {})
    policy_obj = COACHING_POLICIES.get(policy) if isinstance(policy, str) else policy
    if policy_obj is None:
        raise ValueError(f"unknown coaching policy: {policy}")
    try:
        Plan.from_dict(current).validate()
    except ValueError as exc:
        return _result("invalid_input", current, None, None, None, None, [], [], [{"code": "INVALID_INPUT", "detail": str(exc)}], db, policy_obj, planning_policy)
    errors = validate_training_profile(profile, db, relationships)
    if errors:
        return _result("invalid_input", current, None, None, None, None, [], [], [{"code": "INVALID_INPUT", "detail": e} for e in errors], db, policy_obj, planning_policy)
    current_eval = evaluate_plan(current, db, profile, target, relationships)
    if training_state is None:
        if not isinstance(history, TrainingHistory):
            return _result("invalid_input", current, None, current_eval, None, None, [], [], [{"code": "INVALID_INPUT", "detail": "history must be TrainingHistory"}], db, policy_obj, planning_policy)
        as_of = options.get("asOf") or _latest_timestamp(history)
        if not as_of:
            return _result("insufficient_data", current, None, current_eval, None, None, [], [], [{"code": "INSUFFICIENT_HISTORY"}], db, policy_obj, planning_policy)
        state = derive_training_state(_state_for_current(history, current), db, as_of=as_of, window=options.get("window", policy_obj.stateWindowPolicy), timezone=options.get("timezone"), relationships=relationships, target=target)
    else:
        state = _doc(training_state); active = state.get("activePlan", {})
        if active.get("planId") not in (None, current.get("planId")) or active.get("revisionId") not in (None, current.get("revisionId")):
            return _result("invalid_input", current, None, current_eval, None, state, [], [], [{"code": "CONTRADICTORY_TRAINING_STATE"}], db, policy_obj, planning_policy)
    revision = _revision_id(current.get("revisionId"), options.get("revisionId"))
    # Hard profile/equipment/exclusion/availability problems are structural: reuse v1.8.
    if _hard_invalid(current_eval):
        generated = generate_plan(profile, target, db, policy=planning_policy or "full-body-general-v1", training_state=state, relationships=relationships, current_plan=current, options={"planId": current.get("planId"), "revisionId": revision, "name": current.get("name")})
        if generated.get("plan") is None:
            return _result("unsatisfiable", current, None, current_eval, generated.get("evaluation"), state, [], [], generated.get("unsatisfiedConstraints", []), db, policy_obj, planning_policy or "full-body-general-v1")
        decision = {"schemaVersion": "0.1.0", "decisionId": "decision-regenerate", "decisionType": "regenerate_plan", "policyId": policy_obj.policyId, "policyVersion": policy_obj.policyVersion, "planId": current.get("planId"), "revisionId": current.get("revisionId"), "prescriptionId": None, "exerciseId": None, "before": {}, "after": {}, "reasonCodes": ["PLAN_REGENERATION_REQUIRED"], "evidence": {"violations": current_eval["constraints"]["violations"]}, "provenance": state.get("provenance", {})}
        return _result("regeneration_proposed", current, generated["plan"], current_eval, generated["evaluation"], state, [decision], [{"type": "PLAN_REGENERATED", "reasonCodes": ["PLAN_REGENERATION_REQUIRED"], "decisionIds": ["decision-regenerate"]}], [], db, policy_obj, planning_policy or "full-body-general-v1")
    # Progression policies intentionally require the active revision.  Apply
    # their advisory deltas to a copy while it still identifies as current,
    # then assign the immutable proposal its new revision identity.
    candidate = deepcopy(current)
    substitution_decisions, substitution_changes = _substitution_changes(candidate, history if isinstance(history, TrainingHistory) else None, state, profile, db, relationships, policy_obj)
    decisions, changes = _exercise_changes(candidate, state, policy_obj)
    decisions = substitution_decisions + decisions; changes = substitution_changes + changes
    decisions += _adherence_decisions(current, state, policy_obj)
    volume_decisions, volume_changes = _volume_changes(candidate, current_eval, db, policy_obj)
    decisions += volume_decisions; changes += volume_changes
    if not changes:
        frequency_gaps = [muscle for muscle, value in current_eval.get("frequency", {}).items() if value.get("state") == "below_minimum"]
        target_gaps = current_eval["summary"]["targetGaps"]
        # A target minimum that cannot be repaired by a bounded one-set edit is
        # structural for this conservative policy, so reuse the v1.8 generator.
        if frequency_gaps or target_gaps:
            generated = generate_plan(profile, target, db, policy=planning_policy or "full-body-general-v1", training_state=state, relationships=relationships, current_plan=current, options={"planId": current.get("planId"), "revisionId": revision, "name": current.get("name")})
            if generated.get("plan") is not None:
                decision = {"schemaVersion": "0.1.0", "decisionId": "decision-regenerate-target", "decisionType": "regenerate_plan", "policyId": policy_obj.policyId, "policyVersion": policy_obj.policyVersion, "planId": current.get("planId"), "revisionId": current.get("revisionId"), "prescriptionId": None, "exerciseId": None, "before": {}, "after": {}, "reasonCodes": ["PLAN_REGENERATION_REQUIRED"], "evidence": {"frequencyMuscles": frequency_gaps, "targetGaps": target_gaps}, "provenance": state.get("provenance", {})}
                return _result("regeneration_proposed", current, generated["plan"], current_eval, generated["evaluation"], state, decisions + [decision], [], [], db, policy_obj, planning_policy or "full-body-general-v1")
        sparse = not any(x.get("recentSessionCount", 0) for x in state.get("exerciseState", {}).values())
        if sparse:
            decisions.append({"schemaVersion": "0.1.0", "decisionId": "decision-insufficient-history", "decisionType": "insufficient_data", "policyId": policy_obj.policyId, "policyVersion": policy_obj.policyVersion, "planId": current.get("planId"), "revisionId": current.get("revisionId"), "prescriptionId": None, "exerciseId": None, "before": {}, "after": {}, "reasonCodes": ["INSUFFICIENT_HISTORY"], "evidence": {}, "provenance": state.get("provenance", {})})
        return _result("insufficient_data" if sparse else "no_change", current, None, current_eval, None, state, decisions, [], [], db, policy_obj, planning_policy)
    candidate["revisionId"] = revision
    try:
        Plan.from_dict(candidate).validate()
    except ValueError as exc:
        return _result("unsatisfiable", current, None, current_eval, None, state, decisions, changes, [{"code": "INVALID_PROPOSAL", "detail": str(exc)}], db, policy_obj, planning_policy)
    proposed_eval = evaluate_plan(candidate, db, profile, target, relationships)
    if (_hard_invalid(proposed_eval) or proposed_eval["summary"]["targetGaps"] > current_eval["summary"]["targetGaps"]
            or _target_excess_count(proposed_eval) > _target_excess_count(current_eval)):
        return _result("unsatisfiable", current, None, current_eval, proposed_eval, state, decisions, changes, [{"code": "EVALUATOR_GATE_REJECTED"}], db, policy_obj, planning_policy)
    return _result("revision_proposed", current, candidate, current_eval, proposed_eval, state, decisions, changes, [], db, policy_obj, planning_policy)


__all__ = ["CoachingPolicy", "COACHING_POLICIES", "adapt_plan", "COACHING_VERSION"]
