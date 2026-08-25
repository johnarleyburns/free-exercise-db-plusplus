"""The fedbpp command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from . import Database, Plan, VolumeTarget, Workout, analyze_plan, compare_plan_actual, compare_plans, compare_to_targets
from .conversion import ConversionError, export_workout, import_workout
from .interop import MappingRegistry


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
    if args.command == "analyze-plan": return analyze_plan(Plan.load(args.plan), db)
    if args.command == "compare-plans": return compare_plans(Plan.load(args.plan_a), Plan.load(args.plan_b), db)
    if args.command == "compare-actual": return compare_plan_actual(Plan.load(args.plan), Workout.load(args.workout), db)
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
    p = sub.add_parser("analyze-plan"); p.add_argument("plan"); p.add_argument("--db", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-plans"); p.add_argument("plan_a"); p.add_argument("plan_b"); p.add_argument("--db", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-actual"); p.add_argument("plan"); p.add_argument("workout"); p.add_argument("--db", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare-target"); p.add_argument("plan"); p.add_argument("target"); p.add_argument("--db", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("import"); p.add_argument("format"); p.add_argument("input"); p.add_argument("--output"); p.add_argument("--report"); mode = p.add_mutually_exclusive_group(); mode.add_argument("--strict", action="store_true"); mode.add_argument("--allow-lossy", action="store_true")
    p = sub.add_parser("export"); p.add_argument("format"); p.add_argument("input"); p.add_argument("--output"); p.add_argument("--report"); mode = p.add_mutually_exclusive_group(); mode.add_argument("--strict", action="store_true"); mode.add_argument("--allow-lossy", action="store_true")
    p = sub.add_parser("mapping"); ms = p.add_subparsers(dest="mapping_kind", required=True)
    p = ms.add_parser("external"); p.add_argument("system"); p.add_argument("external_id")
    p = ms.add_parser("dbpp"); p.add_argument("exercise_id"); p.add_argument("--system")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate": _validate(args.kind, args.file); return 0
        if args.command in {"analyze-plan", "compare-plans", "compare-actual", "compare-target"}:
            result = _analysis(args)
            if getattr(args, "json", False): _dump(result)
            else: print(json.dumps(result, sort_keys=True, indent=2))
            return 0
        if args.command == "mapping":
            registry = MappingRegistry.load()
            result = registry.lookup_external(args.system, args.external_id) if args.mapping_kind == "external" else registry.lookup_dbpp(args.exercise_id, args.system)
            _dump([m.__dict__ | {"is_ambiguous": m.is_ambiguous} for m in result]); return 0
        mode = "allow-lossy" if args.allow_lossy else "strict"
        if args.command == "import": result = import_workout(args.format, args.input, mode=mode)
        else: result = export_workout(args.format, _load_json(args.input), mode=mode)
        _dump(result.document, args.output); _conversion_report(result, args.report); return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ConversionError) as exc:
        print(f"fedbpp: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
