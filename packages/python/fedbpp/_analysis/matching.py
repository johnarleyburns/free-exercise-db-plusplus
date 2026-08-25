"""Explicit-reference-first matching between PLAN and ACTUAL documents."""
from __future__ import annotations

from typing import Any

STATUSES = ("matched", "substitution", "unplanned_addition", "missing_prescription", "unable_to_match")

def _prescriptions(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {exercise["prescriptionId"]: {**exercise, "planSessionId": session["planSessionId"]}
            for session in plan.get("sessions", []) for exercise in session.get("exercises", [])}

def _session_prescriptions(plan: dict[str, Any], session_id: str) -> dict[str, dict[str, Any]]:
    for session in plan.get("sessions", []):
        if session.get("planSessionId") == session_id:
            return {exercise["prescriptionId"]: exercise for exercise in session.get("exercises", [])}
    return {}

def _exercise_key(exercise: dict[str, Any]) -> str | None:
    return exercise.get("exerciseId")

def match_plan_actual(plan: dict[str, Any], workout: dict[str, Any]) -> dict[str, Any]:
    """Match one ACTUAL session to a PLAN revision using explicit references first."""
    reference = workout.get("planReference") or {}
    if reference.get("planId") != plan.get("planId") or reference.get("revisionId") != plan.get("revisionId"):
        return {"sessionStatus": "unable_to_match", "planSessionId": reference.get("planSessionId"), "exercises": [], "missingPrescriptions": []}
    session_id = reference.get("planSessionId")
    planned = _session_prescriptions(plan, session_id)
    if not planned:
        return {"sessionStatus": "unable_to_match", "planSessionId": session_id, "exercises": [], "missingPrescriptions": []}
    all_prescriptions = _prescriptions(plan)
    matched_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    for index, actual in enumerate(workout.get("exercises", [])):
        explicit = actual.get("exercisePrescriptionId")
        substitution = actual.get("substitution") or {}
        candidate = explicit or substitution.get("plannedPrescriptionId")
        prescription = planned.get(candidate) if candidate else None
        status: str
        reason = None
        if prescription is not None:
            status = "substitution" if substitution else "matched"
            reason = substitution.get("reason") if substitution else None
            matched_ids.add(candidate)
        elif candidate and candidate in all_prescriptions:
            status = "unable_to_match"
            reason = "prescription belongs to a different plan session"
        else:
            same_exercise = [pid for pid, item in planned.items() if pid not in matched_ids and _exercise_key(item) and _exercise_key(item) == _exercise_key(actual)]
            if len(same_exercise) == 1 and not explicit and not substitution:
                candidate = same_exercise[0]; prescription = planned[candidate]; status = "matched"; matched_ids.add(candidate)
            elif explicit or substitution:
                status = "unable_to_match"; reason = "referenced prescription is not in the linked plan session"
            else:
                status = "unplanned_addition"
        matches.append({"actualExerciseIndex": index, "prescriptionId": candidate, "status": status, "reason": reason, "actual": actual, "prescription": prescription})
    missing = [{"prescriptionId": pid, "status": "missing_prescription", "prescription": planned[pid]} for pid in sorted(set(planned) - matched_ids)]
    return {"sessionStatus": "matched", "planSessionId": session_id, "exercises": matches, "missingPrescriptions": missing}

__all__ = ["STATUSES", "match_plan_actual"]
