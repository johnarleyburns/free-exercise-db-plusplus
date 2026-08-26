"""Deterministic v1.8 PLAN proposal generation.

This module deliberately constructs a small, inspectable draft.  It is not an
optimizer and it never changes an active PLAN or applies a coaching decision.
Every returned draft is validated and evaluated by :func:`evaluate_plan`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy
from typing import Any

from ._analysis.policies import set_credits
from ._analysis.targets import validate_target
from .plan import Plan
from .plan_evaluation import evaluate_plan
from .training import validate_training_profile

GENERATOR_VERSION = "0.1.0"


@dataclass(frozen=True)
class PlanningPolicy:
    policyId: str
    policyVersion: str
    description: str
    splitStrategy: str
    exerciseSelectionStrategy: str
    volumeAllocationStrategy: str
    frequencyStrategy: str
    tieBreakingStrategy: str
    parameters: dict[str, Any]

    def document(self) -> dict[str, Any]:
        return asdict(self)


PLANNING_POLICIES: dict[str, PlanningPolicy] = {
    "full-body-general-v1": PlanningPolicy(
        "full-body-general-v1", "1", "Reference deterministic full-body construction policy.",
        "full_body_every_session", "eligible_target_coverage_v1",
        "greatest_deficit_one_set_v1", "least_exposed_session_v1",
        "explicit_tuple_then_exercise_id_v1",
        {"defaultSessionsPerCycle": 3, "setBlock": 1, "reps": {"min": 6, "target": 8, "max": 10},
         "effort": {"rir": 2}, "allowUnverifiableEquipment": False,
         "preferHistoryContinuity": True, "avoidSameFamilyInSession": True},
    )
    ,"upper-lower-general-v1": PlanningPolicy(
        "upper-lower-general-v1", "1", "Reference deterministic alternating upper/lower construction policy.",
        "upper_lower_alternating", "eligible_target_coverage_v1",
        "greatest_deficit_one_set_v1", "least_exposed_compatible_session_v1",
        "explicit_tuple_then_exercise_id_v1",
        {"defaultSessionsPerCycle": 4, "minimumSessionsPerCycle": 2, "setBlock": 1,
         "reps": {"min": 6, "target": 8, "max": 10}, "effort": {"rir": 2},
         "allowUnverifiableEquipment": False, "preferHistoryContinuity": True,
         "upperMuscles": ["chest", "lats", "middle_back", "traps", "biceps", "triceps", "shoulders", "forearms", "rotator_cuff"],
         "lowerMuscles": ["quadriceps", "hamstrings", "glutes", "calves", "abductors", "adductors", "hip_flexors", "lower_back"],
         "upperPatterns": ["horizontal_press", "horizontal_press_triceps_bias", "incline_press", "decline_press", "vertical_press", "horizontal_pull", "vertical_pull", "chest_fly", "elbow_extension", "elbow_flexion", "shoulder_abduction", "shoulder_flexion", "shoulder_external_rotation", "shoulder_internal_rotation", "face_pull", "reverse_fly", "shrug", "upright_row"],
         "lowerPatterns": ["squat", "squat_quad_bias", "lunge", "step_up", "leg_press", "hip_hinge", "hip_extension", "hip_flexion", "knee_extension", "knee_flexion", "plantar_flexion_bent_knee", "plantar_flexion_straight_knee", "hip_abduction", "hip_adduction"]},
    )
}


@dataclass(frozen=True)
class PlanGenerationRequest:
    profile: Any
    target: Any
    db: Any
    policy: str | PlanningPolicy = "full-body-general-v1"
    training_state: Any | None = None
    relationships: Any | None = None
    current_plan: Any | None = None
    requiredExerciseIds: tuple[str, ...] = ()
    lockedExerciseIds: tuple[str, ...] = ()
    additionalExclusions: tuple[str, ...] = ()
    options: dict[str, Any] | None = None


def _doc(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


def _exercise_data(db: Any, eid: str) -> dict[str, Any] | None:
    try:
        value = db.get_exercise(eid) if hasattr(db, "get_exercise") else db.get("exercises", {}).get(eid)
    except KeyError:
        return None
    return value.data if hasattr(value, "data") else value


def _family_id(relationships: Any, eid: str) -> str | None:
    if relationships is None:
        return None
    family = relationships.family_for(eid) if hasattr(relationships, "family_for") else None
    return family.family_id if family else None


def _range(value: Any) -> dict[str, float | None]:
    if not isinstance(value, dict):
        return {"min": None, "target": float(value) if isinstance(value, (int, float)) else None, "max": None}
    return {"min": value.get("min", value.get("minimumSets")), "target": value.get("target", value.get("targetSets")), "max": value.get("max", value.get("maximumSets"))}


def _ids(plan: dict[str, Any] | None) -> set[str]:
    return {rx.get("exerciseId") for s in (plan or {}).get("sessions", []) for rx in s.get("exercises", []) if rx.get("exerciseId")}


def _available_equipment(profile: dict[str, Any]) -> set[str]:
    values = set(profile.get("equipment", []) or [])
    if values & {"bodyweight", "no equipment", "none"}:
        values.add("body only")
    return values


def _candidate_pool(db: Any, profile: dict[str, Any], relationships: Any, required: set[str], extra_excluded: set[str], policy: PlanningPolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    constraints = profile.get("constraints", {}) or {}
    excluded = set(constraints.get("excludedExerciseIds", []) or []) | extra_excluded
    excluded_families = set(constraints.get("excludedFamilyIds", []) or [])
    available = _available_equipment(profile)
    reasons: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for eid in sorted((db._exercises if hasattr(db, "_exercises") else db.get("exercises", {}))):
        data = _exercise_data(db, eid) or {}; annotation = data.get("annotation", {}); family = _family_id(relationships, eid)
        if eid in excluded or (family and family in excluded_families):
            continue
        if not annotation.get("volumeEligible", False):
            continue
        equipment = data.get("source", {}).get("equipment")
        if equipment is None or str(equipment) in {"None", "other"}:
            if not policy.parameters.get("allowUnverifiableEquipment", False):
                continue
        elif equipment == "body only":
            if "body only" not in available:
                continue
        elif equipment not in available:
            continue
        candidates.append({"exerciseId": eid, "name": data.get("name") or data.get("source", {}).get("name") or eid,
                           "annotation": annotation, "familyId": family, "equipment": equipment})
    for eid in sorted(required):
        data = _exercise_data(db, eid)
        if eid in excluded:
            reasons.append({"code": "EXCLUDED_REQUIRED_EXERCISE", "exerciseId": eid})
        elif data is None:
            reasons.append({"code": "NO_ELIGIBLE_EXERCISE", "exerciseId": eid, "detail": "unknown exerciseId"})
        elif not any(c["exerciseId"] == eid for c in candidates):
            reasons.append({"code": "NO_AVAILABLE_EQUIPMENT", "exerciseId": eid})
    return candidates, reasons


def _session_count(profile: dict[str, Any], policy: PlanningPolicy) -> tuple[list[int], list[dict[str, Any]]]:
    av = profile.get("availability", {}) or {}; bounds = av.get("sessionsPerCycle", {}) or {}
    low, high = bounds.get("min", 1), bounds.get("max", None)
    desired = bounds.get("target", policy.parameters["defaultSessionsPerCycle"])
    # A canonical PLAN needs at least one session even though an availability
    # range may express zero training sessions for other application purposes.
    if high == 0:
        return [], [{"code": "SESSION_COUNT_CONFLICT", "detail": "canonical PLAN requires at least one session"}]
    low = max(1, low, int(policy.parameters.get("minimumSessionsPerCycle", 1)))
    if high is not None and low > high:
        return [], [{"code": "SESSION_COUNT_CONFLICT", "minimum": low, "maximum": high}]
    if high is not None and desired > high: desired = high
    if desired < low: desired = low
    values = [n for n in range(low, (high + 1) if high is not None else max(desired, low) + 1)]
    # target, then nearer lower count, then nearer higher count; all explicitly bounded.
    return sorted(values, key=lambda n: (abs(n - desired), 0 if n <= desired else 1, n)), []


def _validate_policy(policy: PlanningPolicy) -> list[str]:
    required = ("defaultSessionsPerCycle", "setBlock", "reps", "allowUnverifiableEquipment")
    errors = []
    if not policy.policyId or not policy.policyVersion:
        errors.append("policyId and policyVersion are required")
    if policy.splitStrategy not in {"full_body_every_session", "upper_lower_alternating"}:
        errors.append("unsupported splitStrategy")
    for key in required:
        if key not in policy.parameters:
            errors.append(f"parameters.{key} is required")
    if isinstance(policy.parameters.get("setBlock"), bool) or not isinstance(policy.parameters.get("setBlock"), int) or policy.parameters.get("setBlock", 0) < 1:
        errors.append("parameters.setBlock must be a positive integer")
    reps = policy.parameters.get("reps")
    if not isinstance(reps, dict) or any(key not in reps for key in ("min", "target", "max")):
        errors.append("parameters.reps must define min, target, and max")
    return sorted(set(errors))


def _session_kind(policy: PlanningPolicy, index: int) -> str:
    if policy.splitStrategy == "upper_lower_alternating":
        return "upper" if index % 2 == 0 else "lower"
    return "full_body"


def _compatible(candidate: dict[str, Any], session_index: int, policy: PlanningPolicy) -> bool:
    kind = _session_kind(policy, session_index)
    if kind == "full_body":
        return True
    ann = candidate["annotation"]
    muscles = set(ann.get("direct", [])) | set(ann.get("indirect", []))
    patterns = set(ann.get("patterns", []))
    return bool(muscles & set(policy.parameters[f"{kind}Muscles"]) or patterns & set(policy.parameters[f"{kind}Patterns"]))


def _day_offsets(cycle_days: int, count: int, preferred: list[int], excluded: set[int], locked: list[int] | None = None) -> list[int] | None:
    allowed = [d for d in range(cycle_days) if d not in excluded]
    if len(allowed) < count:
        return None
    locked = sorted(set(locked or ()))
    if len(locked) > count or any(d not in allowed for d in locked):
        return None
    chosen = locked + [d for d in sorted(set(d for d in preferred if d in allowed)) if d not in locked]
    chosen = chosen[:count]
    while len(chosen) < count:
        # Maximise the nearest circular spacing; lower day offset resolves ties.
        choices = [d for d in allowed if d not in chosen]
        def spacing(d: int) -> int:
            if not chosen: return cycle_days
            return min(min((d - x) % cycle_days, (x - d) % cycle_days) for x in chosen)
        chosen.append(sorted(choices, key=lambda d: (-spacing(d), d))[0])
    return sorted(chosen)


def _locked_locations(current: dict[str, Any] | None, locked: set[str]) -> tuple[dict[str, list[int]], list[dict[str, Any]]]:
    if not locked:
        return {}, []
    if current is None:
        return {}, [{"code": "LOCKED_EXERCISE_CONFLICT", "exerciseId": eid, "detail": "locked exercises require current_plan"} for eid in sorted(locked)]
    locations: dict[str, list[int]] = {eid: [] for eid in locked}
    session_offsets: list[int] = []
    for session in current.get("sessions", []):
        ids = {rx.get("exerciseId") for rx in session.get("exercises", [])}
        selected = ids & locked
        if selected:
            session_offsets.append(session.get("dayOffset"))
            for eid in selected:
                locations[eid].append(session.get("dayOffset"))
    conflicts: list[dict[str, Any]] = []
    for eid in sorted(locked):
        if not locations[eid]:
            conflicts.append({"code": "LOCKED_EXERCISE_CONFLICT", "exerciseId": eid, "detail": "exercise does not occur in current_plan"})
    if len(session_offsets) != len(set(session_offsets)):
        conflicts.append({"code": "LOCKED_EXERCISE_CONFLICT", "detail": "multiple locked current-plan sessions share a dayOffset"})
    return {eid: sorted(set(offsets)) for eid, offsets in locations.items() if offsets}, conflicts


def _new_plan(cycle_days: int, offsets: list[int], policy: PlanningPolicy, options: dict[str, Any]) -> dict[str, Any]:
    base = options.get("planId", "generated-plan")
    revision = options.get("revisionId", "r1")
    return {"schemaVersion": "0.2.0", "planId": base, "revisionId": revision,
            "name": options.get("name", f"Generated {policy.policyId}"), "description": None,
            "cycle": {"lengthDays": cycle_days},
            "sessions": [{"planSessionId": f"session-{i + 1}", "dayOffset": day, "name": (f"{_session_kind(policy, i).replace('_', ' ').title()} {i // 2 + 1}" if _session_kind(policy, i) != "full_body" else f"Session {i + 1}"), "exercises": []} for i, day in enumerate(offsets)]}


def _add(plan: dict[str, Any], session_index: int, candidate: dict[str, Any], policy: PlanningPolicy, reason: str, rationale: dict[str, set[str]]) -> None:
    session = plan["sessions"][session_index]
    existing = next((x for x in session["exercises"] if x.get("exerciseId") == candidate["exerciseId"]), None)
    if existing is not None:
        existing["sets"] = int(existing.get("sets", 0)) + int(policy.parameters["setBlock"])
    else:
        n = len(session["exercises"]) + 1
        session["exercises"].append({"prescriptionId": f"rx-{session_index + 1:02d}-{n:02d}", "exerciseId": candidate["exerciseId"],
            "exerciseName": candidate["name"], "order": n, "sets": int(policy.parameters["setBlock"]),
            "reps": deepcopy(policy.parameters["reps"]), "effort": deepcopy(policy.parameters.get("effort")), "setType": "working"})
    rationale.setdefault(candidate["exerciseId"], set()).add(reason)


def _above_max(evaluation: dict[str, Any]) -> bool:
    for section in (evaluation["muscleCoverage"], evaluation["frequency"], evaluation["movementPatterns"], evaluation["families"]["targets"]):
        if any(row.get("state") == "above_maximum" for row in section.values()):
            return True
    return False


def _deficits(evaluation: dict[str, Any], phase: str) -> list[tuple[float, str, str]]:
    rows: list[tuple[float, str, str]] = []
    for kind, section, actual_key in (("muscle", evaluation["muscleCoverage"], "actualEffectiveSets"), ("frequency", evaluation["frequency"], "normalizedExposuresPer7Days"), ("pattern", evaluation["movementPatterns"], "plannedSets"), ("family", evaluation["families"]["targets"], "plannedSets")):
        for key, row in section.items():
            required = row.get("minimum") if phase == "minimum" else row.get("target")
            actual = row.get(actual_key, 0)
            if required is not None and actual < required:
                rows.append((float(required - actual), kind, key))
    return sorted(rows, key=lambda x: (-x[0], x[1], x[2]))


def _excesses(evaluation: dict[str, Any]) -> list[tuple[float, str, str]]:
    rows: list[tuple[float, str, str]] = []
    for kind, section, actual_key in (("muscle", evaluation["muscleCoverage"], "actualEffectiveSets"), ("frequency", evaluation["frequency"], "normalizedExposuresPer7Days"), ("pattern", evaluation["movementPatterns"], "plannedSets"), ("family", evaluation["families"]["targets"], "plannedSets")):
        for key, row in section.items():
            if row.get("maximum") is not None and row.get(actual_key, 0) > row["maximum"]:
                rows.append((float(row[actual_key] - row["maximum"]), kind, key))
    return sorted(rows, key=lambda x: (-x[0], x[1], x[2]))


def _contributes(candidate: dict[str, Any], kind: str, key: str, credits: dict[str, float]) -> float:
    ann = candidate["annotation"]
    if kind == "muscle":
        return (credits["direct"] if key in ann.get("direct", []) else 0) + (credits["indirect"] if key in ann.get("indirect", []) else 0) + (credits["stabilizer"] if key in ann.get("stabilizers", []) else 0)
    if kind == "pattern": return 1.0 if key in ann.get("patterns", []) else 0.0
    if kind == "family": return 1.0 if candidate.get("familyId") == key else 0.0
    return 1.0 if key in set(ann.get("direct", [])) | set(ann.get("indirect", [])) else 0.0


def generate_plan(profile: Any, target: Any, db: Any, *, policy: str | PlanningPolicy = "full-body-general-v1", training_state: Any | None = None, relationships: Any | None = None, current_plan: Any | None = None, requiredExerciseIds: list[str] | tuple[str, ...] | None = None, lockedExerciseIds: list[str] | tuple[str, ...] | None = None, additionalExclusions: list[str] | tuple[str, ...] | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic PLAN proposal and unchanged canonical evaluation."""
    profile, target = _doc(profile), _doc(target); state = _doc(training_state) if training_state is not None else None
    current = _doc(current_plan) if current_plan is not None else None; options = dict(options or {})
    policy_obj = PLANNING_POLICIES.get(policy) if isinstance(policy, str) else policy
    if policy_obj is None:
        raise ValueError(f"unknown planning policy: {policy}")
    policy_errors = _validate_policy(policy_obj)
    if policy_errors:
        raise ValueError("invalid planning policy configuration: " + "; ".join(policy_errors))
    if not isinstance(profile, dict) or not isinstance(target, dict):
        return {"status": "invalid_input", "plan": None, "evaluation": None, "policy": policy_obj.document(), "selectionRationale": [], "unsatisfiedConstraints": [{"code": "INVALID_INPUT"}], "unsatisfiedTargets": [], "unsatisfiedSoftPreferences": [], "provenance": {"generatorVersion": GENERATOR_VERSION}}
    # TARGET's portable vocabulary deliberately remains evaluator-compatible;
    # a target with no eligible DB++ contribution is a reported gap, not a
    # generator-only vocabulary redesign.
    errors = validate_training_profile(profile, db, relationships) + validate_target(target)
    if target.get("families") and relationships is None:
        errors.append("family targets require exercise relationships")
    if (profile.get("constraints", {}) or {}).get("excludedFamilyIds") and relationships is None:
        errors.append("excluded family constraints require exercise relationships")
    if errors:
        return {"status": "invalid_input", "plan": None, "evaluation": None, "policy": policy_obj.document(), "selectionRationale": [], "unsatisfiedConstraints": [{"code": "INVALID_INPUT", "detail": x} for x in sorted(set(errors))], "unsatisfiedTargets": [], "unsatisfiedSoftPreferences": [], "provenance": {"generatorVersion": GENERATOR_VERSION}}
    if current is not None:
        try:
            Plan.from_dict(current).validate()
        except ValueError as exc:
            return {"status": "invalid_input", "plan": None, "evaluation": None, "policy": policy_obj.document(), "selectionRationale": [], "unsatisfiedConstraints": [{"code": "INVALID_INPUT", "detail": f"current_plan: {exc}"}], "unsatisfiedTargets": [], "unsatisfiedSoftPreferences": [], "provenance": {"generatorVersion": GENERATOR_VERSION}}
    locked = set(lockedExerciseIds or ())
    required = set(requiredExerciseIds or ()) | locked
    locked_locations, lock_conflicts = _locked_locations(current, locked)
    if lock_conflicts:
        return _result("unsatisfiable", None, None, policy_obj, {}, lock_conflicts, [], [], db, profile, target, state, relationships, current)
    candidates, blockers = _candidate_pool(db, profile, relationships, required, set(additionalExclusions or ()), policy_obj)
    blockers = [{"code": "LOCKED_EXERCISE_CONFLICT", "exerciseId": item.get("exerciseId"), "conflict": item["code"], **({"detail": item["detail"]} if item.get("detail") else {})} if item.get("exerciseId") in locked else item for item in blockers]
    if blockers or not candidates:
        blockers += ([] if blockers else [{"code": "NO_ELIGIBLE_EXERCISE"}])
        return _result("unsatisfiable", None, None, policy_obj, {}, blockers, [], [], db, profile, target, state, relationships, current)
    counts, count_errors = _session_count(profile, policy_obj)
    if count_errors:
        return _result("unsatisfiable", None, None, policy_obj, {}, count_errors, [], [], db, profile, target, state, relationships, current)
    av = profile.get("availability", {}) or {}; cycle_days = int(av.get("cycleLengthDays", target.get("periodDays", 7)))
    locked_offsets = sorted({offset for offsets in locked_locations.values() for offset in offsets})
    excluded_offsets = set(av.get("excludedDayOffsets", []) or [])
    if any(not isinstance(offset, int) or offset < 0 or offset >= cycle_days or offset in excluded_offsets for offset in locked_offsets):
        return _result("unsatisfiable", None, None, policy_obj, {}, [{"code": "LOCKED_EXERCISE_CONFLICT", "detail": "locked current-plan dayOffset is unavailable in generated cycle"}], [], [], db, profile, target, state, relationships, current)
    offsets_cache: dict[int, list[int] | None] = {n: _day_offsets(cycle_days, n, av.get("preferredDayOffsets", []) or [], excluded_offsets, locked_offsets) for n in counts}
    feasible = next((n for n in counts if offsets_cache[n] is not None), None)
    if feasible is None:
        return _result("unsatisfiable", None, None, policy_obj, {}, [{"code": "SESSION_COUNT_CONFLICT", "detail": "not enough permitted day offsets"}], [], [], db, profile, target, state, relationships, current)
    plan = _new_plan(cycle_days, offsets_cache[feasible] or [], policy_obj, options); rationale: dict[str, set[str]] = {}
    credits = set_credits(db); existing = _ids(current); prefs = profile.get("exercisePreferences", {}) or {}; preferred = set(prefs.get("preferredExerciseIds", []) or []); avoided = set(prefs.get("avoidedExerciseIds", []) or [])
    preferred_families = set(prefs.get("preferredFamilyIds", []) or []); avoided_families = set(prefs.get("avoidedFamilyIds", []) or [])
    history = (state or {}).get("exerciseState", {}) or {}

    def rank(candidate: dict[str, Any], kind: str, key: str) -> tuple[Any, ...]:
        h = history.get(candidate["exerciseId"], {}) or {}; adherence = (h.get("prescriptionAdherence") or {}).get("setAdherence")
        good_history = candidate["exerciseId"] in history and (adherence is None or adherence >= 0.5)
        return (-int(candidate["exerciseId"] in required), -int(candidate["exerciseId"] in existing), -int(good_history), -int(candidate["exerciseId"] in preferred), -int(candidate.get("familyId") in preferred_families), -_contributes(candidate, kind, key, credits), int(candidate["exerciseId"] in avoided) + int(candidate.get("familyId") in avoided_families), candidate["exerciseId"])

    # Locked exercises retain their current-plan day offset. Required exercises
    # have only a presence constraint and therefore use deterministic placement.
    session_by_offset = {session["dayOffset"]: i for i, session in enumerate(plan["sessions"])}
    for eid in sorted(locked):
        candidate = next(c for c in candidates if c["exerciseId"] == eid)
        for offset in locked_locations[eid]:
            if not _compatible(candidate, session_by_offset[offset], policy_obj):
                return _result("unsatisfiable", None, None, policy_obj, rationale, [{"code": "LOCKED_EXERCISE_CONFLICT", "exerciseId": eid, "dayOffset": offset, "detail": "locked exercise is incompatible with generated split role"}], [], [], db, profile, target, state, relationships, current)
            _add(plan, session_by_offset[offset], candidate, policy_obj, "LOCKED_EXERCISE", rationale)
    for i, eid in enumerate(sorted(required - locked)):
        candidate = next(c for c in candidates if c["exerciseId"] == eid)
        sessions = [index for index in range(feasible) if _compatible(candidate, index, policy_obj)]
        if not sessions:
            return _result("unsatisfiable", None, None, policy_obj, rationale, [{"code": "NO_ELIGIBLE_EXERCISE", "exerciseId": eid, "detail": "required exercise incompatible with split"}], [], [], db, profile, target, state, relationships, current)
        _add(plan, sessions[i % len(sessions)], candidate, policy_obj, "REQUIRED_EXERCISE", rationale)
    evaluation = evaluate_plan(plan, db, profile, target, relationships)
    # Canonical evaluation is intentionally invoked after every allocation block.
    for phase in ("minimum", "target"):
        while True:
            missing = _deficits(evaluation, phase)
            if not missing: break
            _, kind, key = missing[0]
            eligible = sorted((c for c in candidates if _contributes(c, kind, key, credits) > 0), key=lambda c: rank(c, kind, key))
            accepted = False
            for candidate in eligible:
                sessions = [index for index in range(feasible) if _compatible(candidate, index, policy_obj)]
                if kind == "frequency":
                    sessions.sort(key=lambda i: (int(any(key in (rx.get("exerciseId") and (_exercise_data(db, rx["exerciseId"]) or {}).get("annotation", {}).get("direct", []) + (_exercise_data(db, rx["exerciseId"]) or {}).get("annotation", {}).get("indirect", [])) for rx in plan["sessions"][i]["exercises"])), len(plan["sessions"][i]["exercises"]), i))
                else: sessions.sort(key=lambda i: (len(plan["sessions"][i]["exercises"]), i))
                for si in sessions:
                    draft = deepcopy(plan); _add(draft, si, candidate, policy_obj, "TARGET_COVERAGE", {k: set(v) for k, v in rationale.items()})
                    evaluated = evaluate_plan(draft, db, profile, target, relationships)
                    if not _above_max(evaluated):
                        plan, evaluation = draft, evaluated; rationale.setdefault(candidate["exerciseId"], set()).add("TARGET_COVERAGE")
                        if candidate["exerciseId"] in existing: rationale[candidate["exerciseId"]].add("CURRENT_PLAN_CONTINUITY")
                        elif candidate["exerciseId"] in history: rationale[candidate["exerciseId"]].add("HISTORY_CONTINUITY")
                        if candidate["exerciseId"] in preferred: rationale[candidate["exerciseId"]].add("PREFERRED_EXERCISE")
                        if candidate.get("familyId") in preferred_families: rationale[candidate["exerciseId"]].add("PREFERRED_FAMILY")
                        accepted = True; break
                if accepted: break
            if not accepted: break
    # A PLAN schema requires a prescription in each constructed session.  A failure to
    # populate one without breaching target maxima is an explicit hard construction failure.
    for si, session in enumerate(plan["sessions"]):
        if not session["exercises"]:
            compatible = [candidate for candidate in candidates if _compatible(candidate, si, policy_obj)]
            if not compatible:
                return _result("unsatisfiable", None, None, policy_obj, rationale, [{"code": "NO_ELIGIBLE_EXERCISE", "detail": f"no eligible {_session_kind(policy_obj, si)} exercise"}], [], [], db, profile, target, state, relationships, current)
            candidate = sorted(compatible, key=lambda c: rank(c, "muscle", ""))[0]
            draft = deepcopy(plan); _add(draft, si, candidate, policy_obj, "DETERMINISTIC_TIE_BREAK", rationale)
            evaluated = evaluate_plan(draft, db, profile, target, relationships)
            if _above_max(evaluated):
                return _result("unsatisfiable", None, None, policy_obj, rationale, [{"code": "SESSION_COUNT_CONFLICT", "detail": "cannot populate all required sessions without target maximum overshoot"}], [], [], db, profile, target, state, relationships, current)
            plan, evaluation = draft, evaluated
    try:
        Plan.from_dict(plan).validate()
    except ValueError as exc:
        return _result("unsatisfiable", None, None, policy_obj, rationale, [{"code": "INVALID_GENERATED_PLAN", "detail": str(exc)}], [], [], db, profile, target, state, relationships, current)
    if not evaluation["summary"]["satisfiesHardConstraints"]:
        return _result("unsatisfiable", None, evaluation, policy_obj, rationale, [{"code": "EVALUATOR_HARD_CONSTRAINT", "detail": x} for x in evaluation["constraints"]["violations"]], [], [], db, profile, target, state, relationships, current)
    gaps = _deficits(evaluation, "minimum"); excesses = _excesses(evaluation); desired = _deficits(evaluation, "target")
    status = "generated" if not gaps and not excesses else "generated_with_target_gaps"
    selected_ids = _ids(plan); selected_families = {_family_id(relationships, eid) for eid in selected_ids}
    soft: list[dict[str, Any]] = []
    if preferred and not selected_ids & preferred:
        soft.append({"code": "PREFERRED_EXERCISE_UNSATISFIED", "exerciseIds": sorted(preferred)})
    if preferred_families and not selected_families & preferred_families:
        soft.append({"code": "PREFERRED_FAMILY_UNSATISFIED", "familyIds": sorted(preferred_families)})
    if selected_ids & avoided:
        soft.append({"code": "AVOIDED_EXERCISE_USED", "exerciseIds": sorted(selected_ids & avoided)})
    if selected_families & avoided_families:
        soft.append({"code": "AVOIDED_FAMILY_USED", "familyIds": sorted(selected_families & avoided_families)})
    target_reasons = [{"code": _reason_for(kind), "targetId": key, "deficit": deficit} for deficit, kind, key in gaps]
    target_reasons += [{"code": _reason_for(kind).replace("UNSATISFIED", "MAXIMUM_EXCEEDED"), "targetId": key, "excess": excess} for excess, kind, key in excesses]
    return _result(status, plan, evaluation, policy_obj, rationale, [], target_reasons, soft, db, profile, target, state, relationships, current, desired)


def _reason_for(kind: str) -> str:
    return {"muscle": "MUSCLE_TARGET_UNSATISFIED", "frequency": "FREQUENCY_TARGET_UNSATISFIED", "pattern": "PATTERN_TARGET_UNSATISFIED", "family": "FAMILY_TARGET_UNSATISFIED"}[kind]


def _result(status: str, plan: dict[str, Any] | None, evaluation: dict[str, Any] | None, policy: PlanningPolicy, rationale: dict[str, set[str]], constraints: list[dict[str, Any]], targets: list[dict[str, Any]], soft: list[Any], db: Any, profile: dict[str, Any], target: dict[str, Any], state: dict[str, Any] | None, relationships: Any, current: dict[str, Any] | None, desired: list[tuple[float, str, str]] | None = None) -> dict[str, Any]:
    md = db.metadata if hasattr(db, "metadata") else db.get("metadata", {})
    provenance = {"generatorVersion": GENERATOR_VERSION, "policyId": policy.policyId, "policyVersion": policy.policyVersion,
                  "dbSchemaVersion": md.get("schemaVersion"), "dbConverterVersion": md.get("converterVersion"), "dbUpstreamSha256": md.get("upstream", {}).get("sha256"),
                  "trainingProfileSchemaVersion": profile.get("schemaVersion"), "targetSchemaVersion": target.get("schemaVersion"), "trainingStateVersion": state.get("stateVersion") if state else None,
                  "relationshipSchemaVersion": (relationships.document if hasattr(relationships, "document") else relationships or {}).get("schemaVersion") if relationships else None,
                  "analysisPolicy": "dbpp-default-volume-v1", "setCredits": set_credits(db), "evaluationVersion": (evaluation or {}).get("provenance", {}).get("analysisVersion"),
                  "currentPlanRevisionId": current.get("revisionId") if current else None}
    selection = [{"exerciseId": eid, "reasonCodes": sorted(codes)} for eid, codes in sorted(rationale.items())]
    result = {"status": status, "plan": plan, "evaluation": evaluation, "policy": policy.document(), "selectionRationale": selection,
              "unsatisfiedConstraints": constraints, "unsatisfiedTargets": sorted(targets, key=lambda x: (x.get("code", ""), x.get("targetId", ""))), "unsatisfiedSoftPreferences": soft, "provenance": provenance}
    if desired:
        result["unmetTargetValues"] = [{"code": _reason_for(kind), "targetId": key, "deficit": deficit} for deficit, kind, key in desired]
    if plan is not None and current is not None:
        from ._analysis.plan_compare import compare_plans
        comparison = compare_plans(current, plan, db)
        old_ids, new_ids = _ids(current), _ids(plan)
        result["planDifference"] = {"exercisesAdded": sorted(new_ids - old_ids), "exercisesRemoved": sorted(old_ids - new_ids),
                                    "familiesChanged": None if relationships is None else sorted({_family_id(relationships, x) for x in old_ids ^ new_ids if _family_id(relationships, x)}),
                                    "muscleCoverageDelta": comparison["nativeCycle"]["effectiveSets"],
                                    "frequencyDelta": comparison["frequency"]["muscles"]}
    return result


__all__ = ["PlanningPolicy", "PlanGenerationRequest", "PLANNING_POLICIES", "generate_plan"]
