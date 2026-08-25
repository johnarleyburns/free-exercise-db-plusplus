"""Longitudinal PLAN/ACTUAL analysis.

This module deliberately keeps history and its derived tables separate from the
PLAN, ACTUAL, TARGET, and exercise database documents.  It is a small
orchestrator around the v1.1 analysis functions, rather than a second matching
or volume-credit implementation.
"""
from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from ._analysis.coverage import analyze_plan
from ._analysis.plan_actual import analyze_plan_actual
from ._analysis.policies import add_ranges, normalize_range, planned_set_range, scale_range, set_credits

ANALYSIS_VERSION = "1.4.1"
ANALYSIS_POLICY = "dbpp-default-volume-v1"
PERIOD_TYPES = {"calendar_week", "rolling_7_days", "plan_cycle", "phase", "custom_date_range"}
MISSING_STATES = {"zero", "not_prescribed", "not_recorded", "unknown", "unmapped", "volume_ineligible", "not_applicable", "unable_to_match"}


def _doc(value: Any) -> dict[str, Any]:
    return value.document if hasattr(value, "document") else value


@dataclass
class TrainingHistory:
    """Opaque-subject collection of PLAN revisions, ACTUAL sessions, and TARGETs."""

    subject_id: str
    plans: list[Any] = field(default_factory=list)
    workouts: list[Any] = field(default_factory=list)
    targets: list[Any] = field(default_factory=list)
    plan_activations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.subject_id or not isinstance(self.subject_id, str):
            raise ValueError("subject_id must be a non-empty opaque string")
        self.plans = [_doc(x) for x in self.plans]
        self.workouts = [_doc(x) for x in self.workouts]
        self.targets = [_doc(x) for x in self.targets]


SubjectTrainingHistory = TrainingHistory


@dataclass(frozen=True)
class ScheduledOccurrence:
    """Internal identity for one scheduled plan-session occurrence."""

    plan_id: str | None
    revision_id: str | None
    plan_session_id: str | None
    scheduled_date: date
    session: dict[str, Any]
    plan: dict[str, Any]

    @property
    def key(self) -> tuple[Any, ...]:
        return (self.plan_id, self.revision_id, self.plan_session_id, self.scheduled_date)


def _parse_timestamp(value: str | datetime, analyzer_timezone: str | timezone | None = None) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        text = str(value).replace("Z", "+00:00")
        result = datetime.fromisoformat(text)
    if result.tzinfo is None:
        if analyzer_timezone is None:
            raise ValueError("timezone is required for naive ACTUAL timestamps")
        result = result.replace(tzinfo=_tz(analyzer_timezone))
    if analyzer_timezone is not None:
        result = result.astimezone(_tz(analyzer_timezone))
    return result


def _tz(value: str | tzinfo) -> tzinfo:
    if isinstance(value, tzinfo):
        return value
    return ZoneInfo(value)


def _iso(d: date) -> str:
    return d.isoformat()


def _day(value: str | datetime, analyzer_timezone: str | timezone | None) -> date:
    return _parse_timestamp(value, analyzer_timezone).date()


def _range_add(table: dict[str, dict[str, float | None]], key: str, value: Any) -> None:
    table[key] = add_ranges(table.get(key, 0), value)


def _metric_range(coverage: dict[str, Any], role: str, muscle: str) -> dict[str, float | None]:
    names = {"direct": "directSetRanges", "indirect": "indirectSetRanges", "stabilizer": "stabilizerParticipationSetRanges", "effective": "effectiveSetRanges"}
    return normalize_range(coverage.get(names[role], {}).get(muscle, 0))


def _actual_metric(coverage: dict[str, Any], role: str, muscle: str) -> float:
    names = {"direct": "directSets", "indirect": "indirectSets", "stabilizer": "stabilizerParticipationSets", "effective": "effectiveSets"}
    return round(float(coverage.get(names[role], {}).get(muscle, 0)), 6)


def _fraction(actual: float, planned: float | None) -> float | None:
    return round(actual / planned, 6) if planned not in (None, 0) else None


def _target_state(actual: float, target: Mapping[str, Any] | None) -> str:
    if target is None:
        return "not_targeted"
    minimum, desired, maximum = target.get("min"), target.get("target"), target.get("max")
    if minimum is not None and actual < minimum:
        return "below_minimum"
    if maximum is not None and actual > maximum:
        return "above_maximum"
    if desired is None:
        return "within_range"
    if actual < desired:
        return "within_range_below_target"
    if actual > desired:
        return "within_range_above_target"
    return "at_target"


def _activation(history: TrainingHistory, plan: dict[str, Any]) -> dict[str, Any] | None:
    candidates = [x for x in history.plan_activations if x.get("revisionId") == plan.get("revisionId") and x.get("planId", plan.get("planId")) == plan.get("planId")]
    if candidates:
        return candidates[0]
    if plan.get("effectiveFrom") or plan.get("activatedAt"):
        return {"planId": plan.get("planId"), "revisionId": plan.get("revisionId"), "effectiveFrom": plan.get("effectiveFrom", plan.get("activatedAt")), "effectiveTo": plan.get("effectiveTo")}
    return None


def _revision_for(workout: dict[str, Any], history: TrainingHistory, at: datetime, fallback: str | None) -> tuple[dict[str, Any] | None, str]:
    ref = workout.get("planReference") or {}
    if ref.get("revisionId"):
        for plan in history.plans:
            if plan.get("revisionId") == ref.get("revisionId") and (not ref.get("planId") or plan.get("planId") == ref.get("planId")):
                return plan, "explicit"
        return None, "unable_to_match"
    candidates = []
    for plan in history.plans:
        active = _activation(history, plan)
        if not active or not active.get("effectiveFrom"):
            continue
        start = _parse_timestamp(active["effectiveFrom"], at.tzinfo)
        end = _parse_timestamp(active["effectiveTo"], at.tzinfo) if active.get("effectiveTo") else None
        if start <= at and (end is None or at < end):
            candidates.append(plan)
    if len(candidates) == 1:
        return candidates[0], "activation"
    if len(candidates) > 1:
        raise ValueError(f"overlapping plan activation windows for {workout.get('sessionId')}")
    if fallback:
        matches = [p for p in history.plans if p.get("revisionId") == fallback]
        if len(matches) == 1:
            return matches[0], "configured_fallback"
    return None, "unresolved"


def _bounds(start: date, end: date, period: str, tz: timezone, history: TrainingHistory, plan: dict[str, Any] | None) -> list[tuple[date, date]]:
    if period == "custom_date_range":
        return [(start, end)]
    if period == "calendar_week":
        cursor = start - timedelta(days=start.weekday())
        result = []
        while cursor <= end:
            result.append((cursor, cursor + timedelta(days=6)))
            cursor += timedelta(days=7)
        return result
    if period == "rolling_7_days":
        return [(cursor, cursor + timedelta(days=6)) for cursor in (start + timedelta(days=i) for i in range((end - start).days + 1)) if cursor + timedelta(days=6) <= end]
    if period == "plan_cycle":
        length = int((plan or {}).get("cycle", {}).get("lengthDays", 7))
        anchor = _activation(history, plan or {}) if plan else None
        anchor_day = _day(anchor["effectiveFrom"], tz) if anchor and anchor.get("effectiveFrom") else start
        result = []
        cursor = anchor_day
        while cursor <= end:
            finish = cursor + timedelta(days=length - 1)
            if finish >= start:
                result.append((max(cursor, start), min(finish, end)))
            cursor += timedelta(days=length)
        return result
    # phase: phases are expanded from the activation/start anchor.
    phases = (plan or {}).get("phases", [])
    if not phases:
        return _bounds(start, end, "plan_cycle", tz, history, plan)
    anchor = _activation(history, plan or {})
    cursor = _day(anchor["effectiveFrom"], tz) if anchor and anchor.get("effectiveFrom") else start
    out = []
    for phase in phases:
            length = int((phase.get("cycle") or (plan or {}).get("cycle") or {"lengthDays": 7}).get("lengthDays", 7)) * int(phase.get("durationCycles", 1))
            finish = cursor + timedelta(days=length - 1)
            if finish >= start:
                out.append((max(cursor, start), min(finish, end)))
            cursor = finish + timedelta(days=1)
            if cursor > end:
                break
    return out


def _periods(history: TrainingHistory, period: str, start: date, end: date, analyzer_timezone: str | timezone | None) -> list[dict[str, Any]]:
    tz = _tz(analyzer_timezone or "UTC")
    plans = history.plans or [None]
    result: list[dict[str, Any]] = []
    for plan in plans:
        active = _activation(history, plan) if plan else None
        if len(history.plans) > 1 and not active and any(_activation(history, other) for other in history.plans):
            continue
        for pstart, pend in _bounds(start, end, period, tz, history, plan):
            if active and active.get("effectiveFrom"):
                active_start = _day(active["effectiveFrom"], tz)
                active_end = _day(active["effectiveTo"], tz) if active.get("effectiveTo") else None
                if pend < active_start or (active_end is not None and pstart >= active_end):
                    continue
            result.append({"periodType": period, "start": _iso(pstart), "end": _iso(pend), "queryStart": _iso(start), "queryEnd": _iso(end), "timezone": str(analyzer_timezone or "UTC"), "planId": plan.get("planId") if plan else None, "revisionId": plan.get("revisionId") if plan else None, "plan": plan})
    # Revisions share the requested calendar window. Their scheduled contributions
    # are clipped later, so a week crossing a boundary is not double-counted.
    grouped = {}
    for item in result:
        key = (item["start"], item["end"])
        grouped.setdefault(key, []).append(item)
    out = []
    for (pstart, pend), items in sorted(grouped.items()):
        active = [x for x in items if x.get("plan") is not None]
        plans_used = [x["plan"] for x in active]
        first = active[0] if active else items[0]
        out.append({**first, "plan": plans_used[0] if len(plans_used) == 1 else None, "plans": plans_used, "planId": plans_used[0].get("planId") if len(plans_used) == 1 else None, "revisionId": plans_used[0].get("revisionId") if len(plans_used) == 1 else None})
    return out


def _scheduled(plan: dict[str, Any], pstart: date, pend: date, history: TrainingHistory, period: str, tz: timezone) -> list[ScheduledOccurrence]:
    activation = _activation(history, plan)
    anchor = _day(activation["effectiveFrom"], tz) if activation and activation.get("effectiveFrom") else pstart
    cycle = int(plan.get("cycle", {}).get("lengthDays", 7))
    active_start = _day(activation["effectiveFrom"], tz) if activation and activation.get("effectiveFrom") else None
    active_end = _day(activation["effectiveTo"], tz) if activation and activation.get("effectiveTo") else None
    result: list[ScheduledOccurrence] = []
    cursor = anchor
    while cursor <= pend:
        for session in plan.get("sessions", []):
            candidate = cursor + timedelta(days=int(session.get("dayOffset", 0)))
            if pstart <= candidate <= pend and (active_start is None or candidate >= active_start) and (active_end is None or candidate < active_end):
                result.append(ScheduledOccurrence(plan.get("planId"), plan.get("revisionId"), session.get("planSessionId"), candidate, session, plan))
        cursor += timedelta(days=cycle)
    return sorted(result, key=lambda x: (x.scheduled_date, x.plan_session_id or "", x.revision_id or ""))


def _target_for(history: TrainingHistory, at: date, period_days: int) -> dict[str, Any] | None:
    matches = []
    for target in history.targets:
        if target.get("effectiveFrom"):
            start = date.fromisoformat(str(target["effectiveFrom"])[:10])
            end = date.fromisoformat(str(target["effectiveTo"])[:10]) if target.get("effectiveTo") else None
            if start <= at and (end is None or at < end): matches.append(target)
        elif not matches:
            matches.append(target)
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(f"overlapping target windows at {at.isoformat()}")
    target = matches[0]
    source_days = int(target.get("periodDays", period_days)); scale = period_days / source_days
    return {"targetId": target.get("targetId"), "periodDays": period_days, "muscles": {m: scale_range(r, scale) for m, r in target.get("muscles", {}).items()}}


def _target_profiles_for(history: TrainingHistory, start: date, end: date, period_days: int) -> list[dict[str, Any]]:
    profiles = []
    for day in (start + timedelta(days=i) for i in range((end - start).days + 1)):
        profile = _target_for(history, day, period_days)
        if profile and profile.get("targetId") not in {x.get("targetId") for x in profiles}:
            profiles.append(profile)
    return profiles


def _phase_id(plan: dict[str, Any] | None, day: date, history: TrainingHistory, tz: timezone) -> str | None:
    if not plan or not plan.get("phases"): return None
    activation = _activation(history, plan); anchor = _day(activation["effectiveFrom"], tz) if activation and activation.get("effectiveFrom") else day
    elapsed = max(0, (day - anchor).days); cursor = 0
    for phase in plan["phases"]:
        length = int((phase.get("cycle") or plan.get("cycle") or {"lengthDays": 7}).get("lengthDays", 7)) * int(phase.get("durationCycles", 1))
        if elapsed < cursor + length: return phase.get("phaseId")
        cursor += length
    return None


def _rows_for_period(history: TrainingHistory, item: dict[str, Any], db: Any, analyzer_timezone: str | timezone | None, fallback_revision_id: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    tz = _tz(analyzer_timezone or "UTC"); pstart = date.fromisoformat(item["start"]); pend = date.fromisoformat(item["end"])
    qstart = max(pstart, date.fromisoformat(item.get("queryStart", item["start"]))); qend = min(pend, date.fromisoformat(item.get("queryEnd", item["end"])))
    plans = item.get("plans") or ([item["plan"]] if item.get("plan") else [])
    planned = {r: {} for r in ("direct", "indirect", "stabilizer", "effective")}; actual = {r: defaultdict(float) for r in planned}; planned_exposure = defaultdict(float); actual_exposure = defaultdict(float)
    occurrences = [o for plan in plans for o in _scheduled(plan, pstart, pend, history, item["periodType"], tz)]
    session_rows: list[dict[str, Any]] = []; exercise_rows: list[dict[str, Any]] = []; consumed_workouts: set[str] = set(); matched_occurrences: set[tuple[Any, ...]] = set(); planned_mapped = planned_unmapped = 0.0; actual_counted = actual_mapped = actual_unmapped = 0.0
    for occurrence in sorted(occurrences, key=lambda x: x.key):
        one_plan = {**occurrence.plan, "sessions": [occurrence.session], "phases": []}; pc = analyze_plan(one_plan, db); cov = pc["nativeCycle"]
        for role in planned:
            for muscle, value in cov.get({"direct":"directSetRanges", "indirect":"indirectSetRanges", "stabilizer":"stabilizerParticipationSetRanges", "effective":"effectiveSetRanges"}[role], {}).items(): _range_add(planned[role], muscle, value)
        planned_mapped += float(pc["coverageCompleteness"].get("mappedSets", 0)); planned_unmapped += float(pc["coverageCompleteness"].get("unmappedSets", 0))
        for muscle in cov.get("effectiveSetRanges", {}): planned_exposure[muscle] += 1
        selected_workout = None
        for workout in history.workouts:
            sid = workout.get("sessionId")
            if sid in consumed_workouts or not workout.get("startTime"): continue
            stamp = _parse_timestamp(workout["startTime"], analyzer_timezone); ref = workout.get("planReference") or {}
            if stamp.date() != occurrence.scheduled_date or not (qstart <= stamp.date() <= qend): continue
            if ref.get("planSessionId") and ref.get("planSessionId") != occurrence.plan_session_id: continue
            if ref.get("planId") and ref.get("planId") != occurrence.plan_id: continue
            if ref.get("revisionId") and ref.get("revisionId") != occurrence.revision_id: continue
            selected, linkage = _revision_for(workout, history, stamp, fallback_revision_id)
            if selected and selected.get("revisionId") == occurrence.revision_id and selected.get("planId") == occurrence.plan_id:
                selected_workout = workout; break
        if selected_workout is not None:
            ref = selected_workout.get("planReference") or {}; linked = {**selected_workout, "planReference": {**ref, "planId": occurrence.plan_id, "revisionId": occurrence.revision_id, "planSessionId": occurrence.plan_session_id}}
            analysis = analyze_plan_actual(occurrence.plan, linked, db); consumed_workouts.add(selected_workout.get("sessionId")); matched_occurrences.add(occurrence.key)
            session_rows.append(_session_row(history, item, selected_workout, occurrence.plan, occurrence.session, analysis, "matched", occurrence.scheduled_date))
            completeness = analysis.get("totalActualCoverage", {}).get("coverageCompleteness", {}); actual_counted += completeness.get("actualCountedSets", 0); actual_mapped += completeness.get("mappedActualSets", 0); actual_unmapped += completeness.get("unmappedActualSets", 0); _add_actual(analysis, actual, actual_exposure, exercise_rows, history, item, selected_workout, occurrence.plan, occurrence.session)
        else:
            session_rows.append(_session_row(history, item, None, occurrence.plan, occurrence.session, None, "missed_planned_session", occurrence.scheduled_date))
    all_sessions = { (plan.get("planId"), plan.get("revisionId"), s.get("planSessionId")): s for plan in plans for s in plan.get("sessions", []) }
    for workout in history.workouts:
        sid = workout.get("sessionId"); stamp = _parse_timestamp(workout["startTime"], analyzer_timezone) if workout.get("startTime") else None
        if sid in consumed_workouts or stamp is None or not (qstart <= stamp.date() <= qend): continue
        selected, linkage = _revision_for(workout, history, stamp, fallback_revision_id); ref = workout.get("planReference") or {}; status = "unable_to_match" if linkage == "unable_to_match" else "unplanned_session"
        session = all_sessions.get(((selected or {}).get("planId"), (selected or {}).get("revisionId"), ref.get("planSessionId")))
        session_rows.append(_session_row(history, item, workout, selected if session else None, session, None, status, None)); counts = _add_unplanned(workout, actual, actual_exposure, db, exercise_rows, history, item); actual_counted += counts["counted"]; actual_mapped += counts["mapped"]; actual_unmapped += counts["unmapped"]; consumed_workouts.add(sid)
    target_profiles = _target_profiles_for(history, qstart, qend, (pend-pstart).days + 1)
    target = target_profiles[0] if len(target_profiles) == 1 else None
    target_ids = [x.get("targetId") for x in target_profiles]
    plan = plans[0] if len(plans) == 1 else None
    muscles = sorted(set().union(*(set(planned[r]) for r in planned), *(set(actual[r]) for r in actual), *(set((target or {}).get("muscles", {}))), *(set().union(*(set(x.get("muscles", {})) for x in target_profiles)) if target_profiles else set()))); muscle_rows = []
    for muscle in muscles:
        row = {"subject_id": history.subject_id, "period_type": item["periodType"], "period_start": item["start"], "period_end": item["end"], "plan_id": item.get("planId"), "revision_id": item.get("revisionId"), "phase_id": _phase_id(plan, pstart, history, tz), "muscle": muscle, "plan_revisions_used": sorted({x.get("revisionId") for x in plans if x.get("revisionId")}), "plan_ids_used": sorted({x.get("planId") for x in plans if x.get("planId")}), "phase_ids_used": sorted({phase.get("phaseId") for plan_doc in plans for phase in plan_doc.get("phases", []) if phase.get("phaseId")})}
        for role in ("direct", "indirect", "stabilizer", "effective"):
            prescribed = muscle in planned[role]; pr = planned[role].get(muscle, normalize_range(0)); row[f"planned_{role}_min"], row[f"planned_{role}_target"], row[f"planned_{role}_max"] = pr["min"], pr["target"], pr["max"]; row[f"planned_{role}_state"] = "prescribed" if prescribed else "not_prescribed"; av = round(actual[role].get(muscle, 0), 6); row[f"actual_{role}"] = av; row[f"actual_{role}_state"] = "not_recorded" if actual_counted == 0 else "zero" if av == 0 else "recorded"; row[f"{role}_adherence"] = _fraction(av, pr["target"] if pr["target"] is not None else next((pr[k] for k in ("min", "max") if pr[k] is not None), None))
        tr = (target or {}).get("muscles", {}).get(muscle); row.update({"target_min": tr.get("min") if tr else None, "target_target": tr.get("target") if tr else None, "target_max": tr.get("max") if tr else None, "target_state": _target_state(row["actual_effective"], tr) if target else ("mixed_target" if len(target_profiles) > 1 else "not_targeted"), "target_profiles_used": target_ids})
        row.update({"planned_exposures": round(planned_exposure[muscle], 6), "actual_exposures": round(actual_exposure[muscle], 6), "planned_mapped_sets": planned_mapped, "planned_unmapped_sets": planned_unmapped, "actual_mapped_sets": actual_mapped, "actual_unmapped_sets": actual_unmapped, "mapped_fraction": round(actual_mapped / actual_counted, 6) if actual_counted else None, "unplanned_sets": sum(x.get("unplanned_sets", 0) for x in session_rows), "analysis_policy": ANALYSIS_POLICY, "analysis_version": ANALYSIS_VERSION})
        muscle_rows.append(row)
    summary = {"scheduledPlannedSessions": len(occurrences), "completedPlannedSessions": sum(1 for x in session_rows if x["session_status"] == "matched"), "missedPlannedSessions": sum(1 for x in session_rows if x["session_status"] == "missed_planned_session"), "unplannedActualSessions": sum(1 for x in session_rows if x["session_status"] == "unplanned_session"), "sessionAdherenceFraction": round(sum(1 for x in session_rows if x["session_status"] == "matched") / len(occurrences), 6) if occurrences else None, "targetProfilesUsed": target_ids}
    return muscle_rows, sorted(session_rows, key=lambda x: (x["timestamp"] or "", x["session_id"] or "")), sorted(exercise_rows, key=lambda x: (x["session_id"], x["prescription_id"] or "", x["actual_exercise_id"] or "")), summary


def _session_row(history: TrainingHistory, item: dict[str, Any], workout: dict[str, Any] | None, plan: dict[str, Any] | None, session: dict[str, Any] | None, analysis: dict[str, Any] | None, status: str, scheduled_date: date | None = None) -> dict[str, Any]:
    matching = (analysis or {}).get("matching", {}); exercises = matching.get("exercises", [])
    counted = sum(1 for exercise in (workout or {}).get("exercises", []) for item_set in exercise.get("sets", []) if item_set.get("completed") is True and (item_set.get("setType") is None or item_set.get("setType") in {"working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"}))
    planned_ranges = [planned_set_range(x) for x in (session or {}).get("exercises", [])]
    missing = matching.get("missingPrescriptionDetails", [])
    missed_range = normalize_range(0)
    for rx in missing or ((session or {}).get("exercises", []) if status == "missed_planned_session" else []): missed_range = add_ranges(missed_range, planned_set_range(rx))
    planned_range = normalize_range(0)
    for value in planned_ranges: planned_range = add_ranges(planned_range, value)
    actual_sets = sum(float(x.get("actualCompletedSets", 0)) for x in exercises) if analysis else counted
    target_missed = missed_range.get("target")
    return {"subject_id": history.subject_id, "period_type": item["periodType"], "period_start": item["start"], "period_end": item["end"], "scheduled_date": scheduled_date.isoformat() if scheduled_date else None, "session_id": workout.get("sessionId") if workout else None, "timestamp": workout.get("startTime") if workout else None, "plan_id": plan.get("planId") if plan else item.get("planId"), "revision_id": plan.get("revisionId") if plan else item.get("revisionId"), "plan_session_id": session.get("planSessionId") if session else None, "session_status": status, "planned_exercises": len(session.get("exercises", [])) if session else 0, "matched_exercises": sum(1 for x in exercises if x.get("status") == "matched"), "substitutions": sum(1 for x in exercises if x.get("status") == "substitution"), "unplanned_exercises": sum(1 for x in exercises if x.get("status") == "unplanned_addition") if analysis else len((workout or {}).get("exercises", [])), "planned_sets": planned_range.get("target"), "planned_set_min": planned_range.get("min"), "planned_set_max": planned_range.get("max"), "actual_counted_sets": actual_sets, "missing_prescriptions": len(matching.get("missingPrescriptions", [])) if analysis else len((session or {}).get("exercises", [])), "missed_sets": target_missed, "missed_sets_min": missed_range.get("min"), "missed_sets_target": missed_range.get("target"), "missed_sets_max": missed_range.get("max"), "unplanned_sets": sum(float(x.get("actualCompletedSets", 0)) for x in exercises if x.get("status") == "unplanned_addition") if analysis else (counted if status == "unplanned_session" else 0), "session_adherence": 1.0 if status == "matched" else 0.0 if status == "missed_planned_session" else None}


def _add_actual(analysis: dict[str, Any] | None, actual: dict[str, defaultdict[str, float]], exposure: defaultdict[str, float], exercise_rows: list[dict[str, Any]], history: TrainingHistory, item: dict[str, Any], workout: dict[str, Any], plan: dict[str, Any] | None, session: dict[str, Any] | None) -> None:
    if not analysis: return
    for role in actual:
        for muscle, value in analysis.get("totalActualCoverage", {}).get({"direct":"directSets", "indirect":"indirectSets", "stabilizer":"stabilizerParticipationSets", "effective":"effectiveSets"}[role], {}).items(): actual[role][muscle] += float(value)
    for muscle in analysis.get("totalActualCoverage", {}).get("effectiveSets", {}): exposure[muscle] += 1
    for row in analysis.get("matching", {}).get("exercises", []): exercise_rows.append({"subject_id": history.subject_id, "period": item["start"], "session_id": workout.get("sessionId"), "prescription_id": row.get("prescriptionId"), "planned_exercise_id": row.get("plannedExerciseId"), "actual_exercise_id": row.get("actualExerciseId"), "match_status": row.get("status"), "planned_sets_min": row.get("plannedSetRange", {}).get("min"), "planned_sets_target": row.get("plannedSetRange", {}).get("target"), "planned_sets_max": row.get("plannedSetRange", {}).get("max"), "actual_sets": row.get("actualCompletedSets"), "reps_adherence": row.get("reps_adherence"), "load_adherence": row.get("load_adherence"), "rpe_adherence": row.get("rpe_adherence"), "rir_adherence": row.get("rir_adherence"), "set_adherence": row.get("set_adherence"), "volume_load_adherence": row.get("volume_load_adherence"), "substitution_reason": row.get("reason")})


def _add_unplanned(workout: dict[str, Any], actual: dict[str, defaultdict[str, float]], exposure: defaultdict[str, float], db: Any, exercise_rows: list[dict[str, Any]] | None = None, history: TrainingHistory | None = None, item: dict[str, Any] | None = None) -> dict[str, int]:
    # Keep the work recorded without assigning it to a prescription.  Known DB++
    # annotations may contribute to actual totals; unmapped work contributes only
    # to the session-level record.
    before = {role: dict(actual[role]) for role in ("direct", "indirect", "stabilizer")}; counts = {"counted": 0, "mapped": 0, "unmapped": 0}; session_muscles = set()
    for exercise in workout.get("exercises", []):
        try: annotation = db.get_exercise(exercise.get("exerciseId")).annotation
        except (KeyError, AttributeError): annotation = None
        count = sum(1 for s in exercise.get("sets", []) if s.get("completed") is True and (s.get("setType") is None or s.get("setType") in {"working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"}))
        counts["counted"] += count
        if annotation is None:
            counts["unmapped"] += count
            if exercise_rows is not None: exercise_rows.append({"subject_id": history.subject_id if history else None, "period": item.get("start") if item else None, "session_id": workout.get("sessionId"), "prescription_id": None, "planned_exercise_id": None, "actual_exercise_id": exercise.get("exerciseId"), "match_status": "unplanned_addition", "actual_sets": count, "unmapped": True})
            continue
        counts["mapped"] += count
        for role, key in (("direct", "direct"), ("indirect", "indirect"), ("stabilizer", "stabilizers")):
            for muscle in annotation.get(key, []): actual[role][muscle] += count
        session_muscles.update(annotation.get("direct", [])); session_muscles.update(annotation.get("indirect", []))
        if exercise_rows is not None: exercise_rows.append({"subject_id": history.subject_id if history else None, "period": item.get("start") if item else None, "session_id": workout.get("sessionId"), "prescription_id": None, "planned_exercise_id": None, "actual_exercise_id": exercise.get("exerciseId"), "match_status": "unplanned_addition", "actual_sets": count, "unmapped": False})
    for muscle in session_muscles: exposure[muscle] += 1
    credits = set_credits(db)
    for muscle in set(actual["direct"]) | set(actual["indirect"]) | set(actual["stabilizer"]):
        actual["effective"][muscle] += ((actual["direct"].get(muscle, 0) - before["direct"].get(muscle, 0)) * credits["direct"] + (actual["indirect"].get(muscle, 0) - before["indirect"].get(muscle, 0)) * credits["indirect"] + (actual["stabilizer"].get(muscle, 0) - before["stabilizer"].get(muscle, 0)) * credits["stabilizer"])
    return counts


def analyze_periods(history: TrainingHistory, db: Any, period: str = "calendar_week", *, start: str | date | None = None, end: str | date | None = None, timezone: str | timezone | None = None, fallback_revision_id: str | None = None) -> dict[str, Any]:
    if period not in PERIOD_TYPES: raise ValueError(f"unknown period type: {period}")
    stamps = [_parse_timestamp(w["startTime"], timezone) for w in history.workouts if w.get("startTime")]
    if isinstance(start, str): start = date.fromisoformat(start[:10])
    if isinstance(end, str): end = date.fromisoformat(end[:10])
    if start is None: start = min((x.date() for x in stamps), default=date.today())
    if end is None: end = max((x.date() for x in stamps), default=start)
    rows: list[dict[str, Any]] = []; sessions: list[dict[str, Any]] = []; exercises: list[dict[str, Any]] = []; summaries = []
    for item in _periods(history, period, start, end, timezone):
        mr, sr, er, summary = _rows_for_period(history, item, db, timezone, fallback_revision_id); rows.extend(mr); sessions.extend(sr); exercises.extend(er); used = item.get("plans") or ([item["plan"]] if item.get("plan") else []); summaries.append({k: v for k, v in item.items() if k not in {"plan", "plans"}} | {"planRevisionsUsed": sorted({x.get("revisionId") for x in used if x.get("revisionId")}), "planIdsUsed": sorted({x.get("planId") for x in used if x.get("planId")})} | summary)
    metadata = db.metadata if hasattr(db, "metadata") else db.get("metadata", {}); sources = sorted({(w.get("source") or {}).get("system") for w in history.workouts if (w.get("source") or {}).get("system")}); versions = sorted({w.get("schemaVersion") for w in history.workouts if w.get("schemaVersion")})
    provenance = {"analysisVersion": ANALYSIS_VERSION, "analysisPolicy": ANALYSIS_POLICY, "dbSchemaVersion": metadata.get("schemaVersion"), "dbConverterVersion": metadata.get("converterVersion"), "dbSourceSha": (metadata.get("upstream") or {}).get("sha256"), "planSchemaVersions": sorted({p.get("schemaVersion") for p in history.plans if p.get("schemaVersion")}), "workoutSchemaVersions": versions, "targetSchemaVersions": sorted({t.get("schemaVersion") for t in history.targets if t.get("schemaVersion")}), "periodDefinition": period, "timezonePolicy": str(timezone or "UTC; explicit offsets honored"), "setCredits": set_credits(db), "sourceSystemsUsed": sources, "mappingCompleteness": "reported per period"}
    return {"analysisVersion": ANALYSIS_VERSION, "analysisPolicy": ANALYSIS_POLICY, "subjectId": history.subject_id, "periodType": period, "provenance": provenance, "periods": summaries, "musclePeriodRows": sorted(rows, key=lambda x: (x["subject_id"], x["period_start"], x["muscle"])), "sessionRows": sessions, "exerciseRows": exercises}


analyze_history = analyze_periods


def analyze_cohort(histories: Iterable[TrainingHistory], db: Any, period: str = "calendar_week", **kwargs: Any) -> dict[str, Any]:
    histories = list(histories)
    results = [analyze_periods(h, db, period, **kwargs) for h in histories]
    rows = sorted((row for result in results for row in result["musclePeriodRows"]), key=lambda x: (x["subject_id"], x["period_start"], x["muscle"]))
    sessions = sorted((row for result in results for row in result["sessionRows"]), key=lambda x: (x["subject_id"], x["timestamp"] or "", x["session_id"] or ""))
    exercises = sorted((row for result in results for row in result["exerciseRows"]), key=lambda x: (x["subject_id"], x["period"], x["session_id"] or "", x["prescription_id"] or ""))
    return {"analysisVersion": ANALYSIS_VERSION, "analysisPolicy": ANALYSIS_POLICY, "subjects": [h.subject_id for h in histories], "musclePeriodRows": rows, "sessionRows": sessions, "exerciseRows": exercises, "subjectResults": results}


def cohort_summary(result: dict[str, Any], metric: str = "effective_adherence") -> dict[str, float | int | None]:
    values = [float(row[metric]) for row in result.get("musclePeriodRows", []) if row.get(metric) is not None]
    return {"count": len(values), "mean": round(mean(values), 6) if values else None, "median": round(median(values), 6) if values else None, "min": min(values) if values else None, "max": max(values) if values else None}


def _csv(result: dict[str, Any], key: str, destination: str | Path | io.TextIOBase | None = None) -> str | None:
    rows = result.get(key, []); fields = sorted({field for row in rows for field in row})
    # Stable research column order: identifiers first, then the requested fields.
    preferred = {"musclePeriodRows": ["subject_id", "period_type", "period_start", "period_end", "plan_id", "revision_id", "phase_id", "muscle"], "sessionRows": ["subject_id", "period_start", "period_end", "session_id", "timestamp", "plan_id", "revision_id", "plan_session_id", "session_status"], "exerciseRows": ["subject_id", "period", "session_id", "prescription_id", "planned_exercise_id", "actual_exercise_id", "match_status"]}.get(key, [])
    fields = [f for f in preferred if f in fields] + [f for f in fields if f not in preferred]
    stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n"); writer.writeheader(); writer.writerows(rows); text = stream.getvalue()
    if destination is None: return text
    if hasattr(destination, "write"): destination.write(text); return None
    Path(destination).write_text(text, encoding="utf-8"); return None


def export_muscle_period_csv(result: dict[str, Any], destination: str | Path | io.TextIOBase | None = None) -> str | None: return _csv(result, "musclePeriodRows", destination)
def export_session_csv(result: dict[str, Any], destination: str | Path | io.TextIOBase | None = None) -> str | None: return _csv(result, "sessionRows", destination)
def export_exercise_csv(result: dict[str, Any], destination: str | Path | io.TextIOBase | None = None) -> str | None: return _csv(result, "exerciseRows", destination)


__all__ = ["TrainingHistory", "SubjectTrainingHistory", "analyze_history", "analyze_periods", "analyze_cohort", "cohort_summary", "export_muscle_period_csv", "export_session_csv", "export_exercise_csv", "PERIOD_TYPES", "MISSING_STATES"]
