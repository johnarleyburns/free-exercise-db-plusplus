"""The fedbpp command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from . import (Database, Plan, VolumeTarget, Workout, TrainingHistory,
               analyze_plan, compare_plan_actual, compare_plans, compare_to_targets,
               analyze_periods, analyze_cohort, export_muscle_period_csv, export_session_csv,
               export_exercise_csv)
from .conversion import ConversionError, export_workout, import_workout
from .interop import MappingRegistry
from .relationships import RelationshipRegistry


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_history(path: str, *, plans: list[str] | None = None, workouts: list[str] | None = None, targets: list[str] | None = None) -> TrainingHistory:
    value = _load_json(path)
    base = Path(path).resolve().parent
    def load_ref(name: str) -> dict[str, Any]:
        ref = Path(name)
        return _load_json(str(ref if ref.is_absolute() else base / ref))
    def docs(names: list[str] | None, key: str) -> list[dict[str, Any]]:
        if names: return [load_ref(name) for name in names]
        return [(load_ref(name) if isinstance(name, str) else name) for name in value.get(key, [])]
    return TrainingHistory(value.get("subjectId", value.get("subject_id", "")), plans=docs(plans, "plans"), workouts=docs(workouts, "workouts"), targets=docs(targets, "targets"), plan_activations=value.get("planActivations", value.get("plan_activations", [])))


def _dump(value: Any, path: str | None = None) -> None:
    text = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _validate(kind: str, path: str) -> None:
    value = _load_json(path)
    if kind == "db":
        if not isinstance(value.get("exercises"), dict): raise ValueError("database.exercises must be an object")
        print(f"valid database: {path}")
    elif kind == "workout": Workout.from_dict(value).validate(); print(f"valid workout: {path}")
    elif kind == "plan": Plan.from_dict(value).validate(); print(f"valid plan: {path}")
    elif kind == "target": VolumeTarget.from_dict(value).validate(); print(f"valid target: {path}")


def _analysis(args: argparse.Namespace) -> Any:
    db = Database.load(args.db)
    relationships = RelationshipRegistry.load(args.relationships, db=db) if getattr(args,"relationships",None) else None
    if args.command == "analyze-plan": return analyze_plan(Plan.load(args.plan), db, relationships)
    if args.command == "compare-plans": return compare_plans(Plan.load(args.plan_a), Plan.load(args.plan_b), db, relationships)
    if args.command == "compare-actual": return compare_plan_actual(Plan.load(args.plan), Workout.load(args.workout), db, relationships)
    return compare_to_targets(Plan.load(args.plan), VolumeTarget.load(args.target), db)


def _conversion_report(result: Any, path: str | None) -> None:
    if path: _dump(result.report(), path)
    if result.warnings: print("conversion warnings: " + "; ".join(result.warnings), file=sys.stderr)
    if result.losses: print("conversion losses: " + "; ".join(x["reason"] for x in result.losses), file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fedbpp", description="Free Exercise DB++ validation, analysis, and interoperability")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); vs = validate.add_subparsers(dest="kind", required=True)
    for kind in ("db", "workout", "plan", "target"):
        p = vs.add_parser(kind); p.add_argument("file")
    p = sub.add_parser("analyze-plan"); p.add_argument("plan"); p.add_argument("--db", required=True); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-plans"); p.add_argument("plan_a"); p.add_argument("plan_b"); p.add_argument("--db", required=True); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-actual"); p.add_argument("plan"); p.add_argument("workout"); p.add_argument("--db", required=True); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-target"); p.add_argument("plan"); p.add_argument("target"); p.add_argument("--db", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("analyze-history"); p.add_argument("history"); p.add_argument("--db", required=True); p.add_argument("--period", default="calendar_week"); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--timezone"); p.add_argument("--output"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("research-export"); p.add_argument("history"); p.add_argument("--db", required=True); p.add_argument("--period", default="calendar_week"); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--timezone"); p.add_argument("--output", required=True); p.add_argument("--table", choices=("muscle", "session", "exercise"), default="muscle")
    p = sub.add_parser("import"); p.add_argument("format"); p.add_argument("input"); p.add_argument("--output"); p.add_argument("--report"); mode = p.add_mutually_exclusive_group(); mode.add_argument("--strict", action="store_true"); mode.add_argument("--allow-lossy", action="store_true")
    p = sub.add_parser("export"); p.add_argument("format"); p.add_argument("input"); p.add_argument("--output"); p.add_argument("--report"); mode = p.add_mutually_exclusive_group(); mode.add_argument("--strict", action="store_true"); mode.add_argument("--allow-lossy", action="store_true")
    p = sub.add_parser("mapping"); ms = p.add_subparsers(dest="mapping_kind", required=True)
    p = ms.add_parser("external"); p.add_argument("system"); p.add_argument("external_id")
    p = ms.add_parser("dbpp"); p.add_argument("exercise_id"); p.add_argument("--system")
    p = sub.add_parser("family"); p.add_argument("exercise_id"); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("family-members"); p.add_argument("family_id"); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("related"); p.add_argument("exercise_id"); p.add_argument("--relationships"); p.add_argument("--same-family", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-exercises"); p.add_argument("exercise_a"); p.add_argument("exercise_b"); p.add_argument("--db", required=True); p.add_argument("--relationships"); p.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate": _validate(args.kind, args.file); return 0
        if args.command in {"analyze-plan", "compare-plans", "compare-actual", "compare-target"}:
            result = _analysis(args)
            if getattr(args, "json", False): _dump(result)
            else: print(json.dumps(result, sort_keys=True, indent=2))
            return 0
        if args.command in {"analyze-history", "research-export"}:
            manifest = _load_json(args.history)
            db = Database.load(args.db)
            if isinstance(manifest, list):
                histories = []
                manifest_base = Path(args.history).resolve().parent
                def manifest_doc(name: Any) -> Any:
                    if not isinstance(name, str): return name
                    ref = Path(name); return _load_json(str(ref if ref.is_absolute() else manifest_base / ref))
                for entry in manifest:
                    # Reuse the manifest loader without requiring a second file.
                    histories.append(TrainingHistory(entry.get("subjectId", entry.get("subject_id", "")), plans=[manifest_doc(x) for x in entry.get("plans", [])], workouts=[manifest_doc(x) for x in entry.get("workouts", [])], targets=[manifest_doc(x) for x in entry.get("targets", [])], plan_activations=entry.get("planActivations", [])))
                result = analyze_cohort(histories, db, args.period, start=args.start, end=args.end, timezone=args.timezone)
            else:
                result = analyze_periods(_load_history(args.history), db, args.period, start=args.start, end=args.end, timezone=args.timezone)
            if args.command == "analyze-history":
                _dump(result, args.output if not getattr(args, "json", False) else None)
            else:
                exporters = {"muscle": export_muscle_period_csv, "session": export_session_csv, "exercise": export_exercise_csv}
                exporters[args.table](result, args.output)
            return 0
        if args.command == "mapping":
            registry = MappingRegistry.load()
            result = registry.lookup_external(args.system, args.external_id) if args.mapping_kind == "external" else registry.lookup_dbpp(args.exercise_id, args.system)
            _dump([m.__dict__ | {"is_ambiguous": m.is_ambiguous} for m in result]); return 0
        if args.command in {"family", "family-members", "related", "compare-exercises"}:
            registry = RelationshipRegistry.load(args.relationships)
            if args.command == "family":
                family = registry.family_for(args.exercise_id); result = None if family is None else family.__dict__
            elif args.command == "family-members": result = registry.exercises_in_family(args.family_id)
            elif args.command == "related": result = [r.__dict__ for r in registry.related_exercises(args.exercise_id, same_family=True)]
            else:
                registry.db = Database.load(args.db); result = registry.compare_exercise_coverage(args.exercise_a, args.exercise_b)
            _dump(result); return 0
        mode = "allow-lossy" if args.allow_lossy else "strict"
        if args.command == "import": result = import_workout(args.format, args.input, mode=mode)
        else: result = export_workout(args.format, _load_json(args.input), mode=mode)
        _dump(result.document, args.output); _conversion_report(result, args.report); return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ConversionError) as exc:
        print(f"fedbpp: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
