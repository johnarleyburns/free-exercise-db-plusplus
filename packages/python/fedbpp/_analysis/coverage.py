"""Deterministic PLAN coverage analysis using DB++ set-credit semantics."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .policies import planned_set_count


def _number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("target", "min", "max"):
            if key in value:
                return float(value[key])
    raise ValueError(f"cannot determine numeric prescription value from {value!r}")



def _exercise(db: Any, exercise_id: str) -> Any:
    if hasattr(db, "get_exercise"):
        return db.get_exercise(exercise_id)
    record = db["exercises"][exercise_id]
    return record


def _annotation(exercise: Any) -> dict[str, Any]:
    if hasattr(exercise, "annotation"):
        return exercise.annotation
    return exercise.get("annotation", {})


def _db_schema_version(db: Any) -> str | None:
    metadata = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
    return metadata.get("schemaVersion")


def analyze_plan(plan: dict[str, Any], db: Any) -> dict[str, Any]:
    """Expand planned set counts into native and explicit 7-day coverage views.

    Ranged set counts use target, then min, then max. Reps do not multiply set
    coverage. Unknown/custom exercises are retained as unmapped and contribute no
    inferred muscle or movement-pattern coverage.
    """
    cycle_days = int(plan["cycle"]["lengthDays"])
    direct = defaultdict(float)
    indirect = defaultdict(float)
    stabilizers = defaultdict(float)
    patterns = defaultdict(float)
    planned_sets = mapped_sets = unmapped_sets = ineligible_sets = 0.0
    unmapped_prescriptions: list[str] = []
    ineligible_prescriptions: list[str] = []
    for session in plan.get("sessions", []):
        for prescription in session.get("exercises", []):
            sets = planned_set_count(prescription)
            planned_sets += sets
            exercise_id = prescription.get("exerciseId")
            if not exercise_id:
                unmapped_sets += sets
                unmapped_prescriptions.append(prescription["prescriptionId"])
                continue
            try:
                exercise = _exercise(db, exercise_id)
            except (KeyError, TypeError):
                unmapped_sets += sets
                unmapped_prescriptions.append(prescription["prescriptionId"])
                continue
            mapped_sets += sets
            ann = _annotation(exercise)
            if not bool(ann.get("volumeEligible", False)):
                ineligible_sets += sets
                ineligible_prescriptions.append(prescription["prescriptionId"])
            for muscle in ann.get("direct", []):
                direct[muscle] += sets
            for muscle in ann.get("indirect", []):
                indirect[muscle] += sets
            for muscle in ann.get("stabilizers", []):
                stabilizers[muscle] += sets
            for pattern in ann.get("patterns", []):
                patterns[pattern] += sets
    effective = defaultdict(float)
    for muscle in set(direct) | set(indirect) | set(stabilizers):
        effective[muscle] = direct[muscle] + indirect[muscle] * 0.5 + stabilizers[muscle] * 0.0
    def clean(values: dict[str, float]) -> dict[str, float]:
        return {key: round(values[key], 6) for key in sorted(values) if values[key] != 0}
    def view(scale: float = 1.0) -> dict[str, Any]:
        return {
            "directSets": clean({key: value * scale for key, value in direct.items()}),
            "indirectSets": clean({key: value * scale for key, value in indirect.items()}),
            "stabilizerParticipationSets": clean({key: value * scale for key, value in stabilizers.items()}),
            "effectiveSets": clean({key: value * scale for key, value in effective.items()}),
            "movementPatternSets": clean({key: value * scale for key, value in patterns.items()}),
        }
    scale = 7.0 / cycle_days
    result = {
        "analysisVersion": "0.2.0" if plan.get("phases") or plan.get("schemaVersion") == "0.2.0" else "0.1.0",
        "plan": {"planId": plan.get("planId"), "revisionId": plan.get("revisionId")},
        "analysisMetadata": {
            "dbSchemaVersion": _db_schema_version(db),
            "planSchemaVersion": plan.get("schemaVersion"),
            "setCreditPolicy": "dbpp-default",
            "directCredit": 1.0, "indirectCredit": 0.5, "stabilizerCredit": 0.0,
            "nativePeriodDays": cycle_days, "normalizedPeriodDays": 7,
            "setCountPolicy": "target-then-min-then-max",
        },
        "coverageCompleteness": {
            "plannedSets": round(planned_sets, 6), "mappedSets": round(mapped_sets, 6),
            "unmappedSets": round(unmapped_sets, 6), "ineligibleSets": round(ineligible_sets, 6),
            "mappedFraction": round(mapped_sets / planned_sets, 6) if planned_sets else 1.0,
            "unmappedPrescriptions": sorted(unmapped_prescriptions),
            "ineligiblePrescriptions": sorted(ineligible_prescriptions),
        },
        "nativeCycle": {"periodDays": cycle_days, **view()},
        "normalized7Day": {"periodDays": 7, **view(scale)},
    }
    phases = plan.get("phases", [])
    if phases:
        phase_results = []
        for phase in phases:
            phase_sessions = [session for session in plan.get("sessions", []) if session.get("phaseId") == phase.get("phaseId")]
            phase_plan = {**plan, "phases": [], "sessions": phase_sessions}
            phase_result = analyze_plan(phase_plan, db)
            phase_results.append({"phaseId": phase["phaseId"], "durationCycles": phase["durationCycles"], "nativeCycle": phase_result["nativeCycle"], "normalized7Day": phase_result["normalized7Day"]})
        effective_by_phase = {item["phaseId"]: item["nativeCycle"]["effectiveSets"] for item in phase_results}
        muscles = sorted({muscle for values in effective_by_phase.values() for muscle in values})
        result["periodization"] = {
            "phases": phase_results,
            "effectiveSetsByPhase": effective_by_phase,
            "effectiveSetsMinByMuscle": {muscle: round(min(values.get(muscle, 0.0) for values in effective_by_phase.values()), 6) for muscle in muscles},
            "effectiveSetsMaxByMuscle": {muscle: round(max(values.get(muscle, 0.0) for values in effective_by_phase.values()), 6) for muscle in muscles},
            "effectiveSetsAverageByMuscle": {muscle: round(sum(values.get(muscle, 0.0) for values in effective_by_phase.values()) / len(effective_by_phase), 6) for muscle in muscles},
        }
    return result
