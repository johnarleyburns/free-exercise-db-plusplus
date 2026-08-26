"""Deterministic v1.6 PLAN evaluation built on canonical PLAN coverage."""
from __future__ import annotations
from typing import Any

from ._analysis.coverage import analyze_plan
from ._analysis.targets import compare_to_targets
from ._analysis.policies import normalize_range, representative_scalar

EVALUATION_VERSION = "0.1.0"
EVALUATION_POLICY = "plan-evaluation-v1"

def _doc(value: Any) -> dict[str, Any]: return value.document if hasattr(value, "document") else value
def _exercise(db: Any, eid: str) -> Any:
    try: return db.get_exercise(eid) if hasattr(db, "get_exercise") else db.get("exercises", {}).get(eid)
    except KeyError: return None
def _data(ex: Any) -> dict[str, Any]: return ex.data if hasattr(ex, "data") else ex
def _range_value(value: Any) -> dict[str, float | None]:
    if not isinstance(value, dict): return {"min": None, "target": float(value) if isinstance(value, (int, float)) else None, "max": None}
    return {"min": value.get("min", value.get("minimumSets")), "target": value.get("target", value.get("targetSets")), "max": value.get("max", value.get("maximumSets"))}
def _state(actual: float, target: dict[str, float | None]) -> str:
    if target.get("min") is not None and actual < target["min"]: return "below_minimum"
    if target.get("max") is not None and actual > target["max"]: return "above_maximum"
    if target.get("target") is None: return "within_range"
    if actual == target["target"]: return "at_target"
    return "within_range_below_target" if actual < target["target"] else "within_range_above_target"
def _finding(kind: str, **values: Any) -> dict[str, Any]: return {"type": kind, **{key: values[key] for key in sorted(values)}}

def _profile_findings(plan: dict[str, Any], db: Any, profile: dict[str, Any], relationships: Any) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    prefs = profile.get("exercisePreferences", {}) or {}; constraints = profile.get("constraints", {}) or {}
    preferred_ex = set(prefs.get("preferredExerciseIds", [])); avoided_ex = set(prefs.get("avoidedExerciseIds", []))
    preferred_fam = set(prefs.get("preferredFamilyIds", [])); avoided_fam = set(prefs.get("avoidedFamilyIds", []))
    excluded_ex = set(constraints.get("excludedExerciseIds", [])); excluded_fam = set(constraints.get("excludedFamilyIds", []))
    used_ex = []; hard = []; soft = []; supported = []; unsupported = []; unknown = []
    available = set(profile.get("equipment", []) or [])
    body = {"body only", "bodyweight", "no equipment", "none"}
    for session in plan.get("sessions", []):
        sid = session.get("planSessionId")
        for rx in session.get("exercises", []):
            eid = rx.get("exerciseId"); used_ex.append(eid) if eid else None
            ex = _exercise(db, eid) if eid else None
            family = relationships.family_for(eid).family_id if relationships is not None and eid and relationships.family_for(eid) else None
            if eid in excluded_ex: hard.append(_finding("excluded_exercise", exerciseId=eid, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if family in excluded_fam: hard.append(_finding("excluded_family", exerciseId=eid, familyId=family, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if eid in preferred_ex: soft.append(_finding("preferred_exercise_used", exerciseId=eid, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if eid in avoided_ex: soft.append(_finding("avoided_exercise_used", exerciseId=eid, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if family in preferred_fam: soft.append(_finding("preferred_family_used", exerciseId=eid, familyId=family, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if family in avoided_fam: soft.append(_finding("avoided_family_used", exerciseId=eid, familyId=family, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            if ex is None: unknown.append(_finding("unknown_exercise", exerciseId=eid, prescriptionId=rx.get("prescriptionId"), sessionId=sid)); continue
            equipment = _data(ex).get("source", {}).get("equipment")
            if equipment is None or str(equipment) in {"None", "other"}:
                unknown.append(_finding("unknown_equipment", exerciseId=eid, equipment=equipment, prescriptionId=rx.get("prescriptionId"), sessionId=sid))
            elif str(equipment) in body and (available & body): supported.append(eid)
            elif equipment in available: supported.append(eid)
            else: unsupported.append(_finding("unsupported_equipment", equipment=equipment, exerciseId=eid, prescriptionId=rx.get("prescriptionId"), sessionId=sid)); hard.append(unsupported[-1])
    equipment = {"supportedExercises": sorted(set(supported)), "unsupportedExercises": sorted(unsupported, key=lambda x: (x.get("exerciseId") or "", x.get("sessionId") or "", x.get("prescriptionId") or "")), "unknownEquipmentExercises": sorted(unknown, key=lambda x: (x.get("exerciseId") or "", x.get("sessionId") or "", x.get("prescriptionId") or ""))}
    preferences = {"preferredExercisesUsed": sorted({x["exerciseId"] for x in soft if x["type"] == "preferred_exercise_used"}), "preferredFamiliesUsed": sorted({x["familyId"] for x in soft if x["type"] == "preferred_family_used"}), "avoidedExercisesUsed": sorted({x["exerciseId"] for x in soft if x["type"] == "avoided_exercise_used"}), "avoidedFamiliesUsed": sorted({x["familyId"] for x in soft if x["type"] == "avoided_family_used"}), "findings": sorted(soft, key=lambda x: (x["type"], x.get("exerciseId") or x.get("familyId") or "", x.get("sessionId") or "", x.get("prescriptionId") or ""))}
    return equipment, preferences, hard, soft

def evaluate_plan(plan: Any, db: Any, profile: Any = None, target: Any = None, relationships: Any = None) -> dict[str, Any]:
    plan, db = _doc(plan), db
    profile = _doc(profile) if profile is not None else None; target = _doc(target) if target is not None else None
    coverage = analyze_plan(plan, db)
    muscle = {}
    if target is not None:
        comparison = compare_to_targets(plan, target, db)
        muscle = comparison["muscles"]
    frequency = {}
    if target is not None:
        for muscle_id, spec in sorted((target.get("frequency", {}).get("muscles", {}) or {}).items()):
            planned = coverage["exposureFrequency"]["muscles"].get(muscle_id, {"exposuresPerNativeCycle": 0, "normalizedExposuresPer7Days": 0})
            limits = _range_value(spec); actual = planned["normalizedExposuresPer7Days"]
            frequency[muscle_id] = {"plannedExposuresPerNativeCycle": planned["exposuresPerNativeCycle"], "normalizedExposuresPer7Days": actual, "minimum": limits["min"], "target": limits["target"], "maximum": limits["max"], "state": _state(actual, limits)}
    patterns = {}
    pattern_targets = target.get("movementPatterns", {}) if target else {}
    for pattern_id, spec in sorted(pattern_targets.items()):
        actual = coverage["nativeCycle"]["movementPatternSets"].get(pattern_id, 0); limits = _range_value(spec)
        patterns[pattern_id] = {"plannedSets": actual, "minimum": limits["min"], "target": limits["target"], "maximum": limits["max"], "state": _state(actual, limits)}
    families = {}
    if relationships is not None:
        from .relationships import family_coverage
        family_data = family_coverage(plan, relationships)
        for family_id, spec in sorted((target.get("families", {}) if target else {}).items()):
            actual = family_data.get(family_id, {}).get("plannedSets", 0); limits = _range_value(spec)
            families[family_id] = {"plannedSets": actual, "minimum": limits["min"], "target": limits["target"], "maximum": limits["max"], "state": _state(actual, limits)}
        family_section = {key: family_data[key] for key in sorted(family_data)}
    else: family_section = {"available": False, "reason": "relationship artifact not provided"}
    equipment = preferences = {"findings": []}; hard = []
    if profile is not None: equipment, preferences, hard, _ = _profile_findings(plan, db, profile, relationships)
    availability = {"plannedSessions": len(plan.get("sessions", []))}
    if profile is not None and profile.get("availability"):
        av = profile["availability"]; limits = av.get("sessionsPerCycle", {}) or {}; planned = len(plan.get("sessions", [])); availability.update({"min": limits.get("min"), "target": limits.get("target"), "max": limits.get("max"), "state": _state(planned, _range_value(limits))})
        excluded_days = set(av.get("excludedDayOffsets", [])); hard.extend(_finding("excluded_day_offset", sessionId=s.get("planSessionId"), dayOffset=s.get("dayOffset")) for s in plan.get("sessions", []) if s.get("dayOffset") in excluded_days)
    else: availability["state"] = "not_evaluated"
    exercise_counts = {}
    if profile is not None:
        limits = _range_value((profile.get("availability", {}) or {}).get("exercisesPerSession", {}))
        if any(value is not None for value in limits.values()):
            for session in plan.get("sessions", []):
                count = len(session.get("exercises", [])); state = _state(count, limits)
                exercise_counts[session.get("planSessionId")] = {"exerciseCount": count, "minimum": limits["min"], "target": limits["target"], "maximum": limits["max"], "state": state}
                if state in {"below_minimum", "above_maximum"}: hard.append(_finding("exercise_count", sessionId=session.get("planSessionId"), exerciseCount=count, minimum=limits["min"], maximum=limits["max"]))
                elif limits["target"] is not None and count != limits["target"]: preferences.setdefault("findings", []).append(_finding("exercise_count_target_miss", sessionId=session.get("planSessionId"), exerciseCount=count, target=limits["target"]))
    target_gaps = [x for x in muscle.values() if x.get("state") == "below_minimum"] + [x for x in frequency.values() if x.get("state") == "below_minimum"] + [x for x in patterns.values() if x.get("state") == "below_minimum"] + [x for x in families.values() if x.get("state") == "below_minimum"]
    completeness = coverage["coverageCompleteness"]
    warnings = []
    if completeness.get("unmappedSets", 0) or completeness.get("ineligibleSets", 0) or equipment.get("unknownEquipmentExercises"): warnings.append("coverage is incomplete for one or more PLAN exercises")
    if profile and profile.get("availability", {}).get("minutesPerSession"): warnings.append("duration estimation is not evaluated by duration-estimation-v1 because PLAN rest/transition inputs are not complete")
    if target and target.get("families") and relationships is None: warnings.append("family targets cannot be evaluated because relationship artifact was not provided")
    md = coverage["analysisMetadata"]; dbmd = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
    prov = {"analysisVersion": EVALUATION_VERSION, "analysisPolicy": EVALUATION_POLICY, "planSchemaVersion": plan.get("schemaVersion"), "profileSchemaVersion": profile.get("schemaVersion") if profile else None, "targetSchemaVersion": target.get("schemaVersion") if target else None, "relationshipSchemaVersion": relationships.document.get("schemaVersion") if hasattr(relationships, "document") else (relationships.get("schemaVersion") if relationships else None), "dbSchemaVersion": md.get("dbSchemaVersion"), "dbConverterVersion": md.get("dbConverterVersion"), "dbUpstreamSha256": md.get("dbUpstreamSha256"), "setCredits": md.get("setCredits"), "durationPolicy": "duration-estimation-v1" if profile and profile.get("availability", {}).get("minutesPerSession") else None}
    # Prefer the canonical provenance keys when DB++ metadata is present.
    for key in ("schemaVersion", "converterVersion"):
        if prov["db" + ("SchemaVersion" if key == "schemaVersion" else "ConverterVersion")] is None: prov["db" + ("SchemaVersion" if key == "schemaVersion" else "ConverterVersion")] = dbmd.get(key)
    if prov["dbUpstreamSha256"] is None: prov["dbUpstreamSha256"] = dbmd.get("upstream", {}).get("sha256")
    hard = sorted(hard, key=lambda x: (x["type"], x.get("exerciseId") or x.get("familyId") or x.get("sessionId") or "", x.get("sessionId") or "", x.get("prescriptionId") or ""))
    status = "hard_constraint_violation" if hard else ("incomplete_coverage" if completeness.get("mappedFraction", 1) < 1 or (target and target.get("families") and relationships is None) else ("valid_with_target_gaps" if target_gaps else "valid"))
    return {"summary": {"hardConstraintViolations": len(hard), "targetGaps": len(target_gaps), "softPreferenceWarnings": len(preferences.get("findings", [])), "satisfiesHardConstraints": not hard, "meetsTargetMinimums": not target_gaps, "evaluationStatus": status}, "muscleCoverage": muscle, "frequency": frequency, "movementPatterns": patterns, "families": {"coverage": family_section, "targets": families}, "equipment": equipment, "availability": availability, "exerciseCounts": exercise_counts, "preferences": preferences, "constraints": {"violations": hard}, "coverageCompleteness": completeness, "warnings": sorted(set(warnings)), "provenance": prov}

__all__ = ["evaluate_plan"]
