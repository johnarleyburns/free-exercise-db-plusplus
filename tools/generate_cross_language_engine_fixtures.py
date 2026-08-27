"""Author the v1.11 cross-language engine fixtures from the Python oracle.

This is intentionally a small, deterministic authoring tool.  Native
implementations consume the JSON artifacts; they do not execute this tool.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "python"))

from fedbpp import (  # noqa: E402
    Database,
    RelationshipRegistry,
    TrainingHistory,
    adapt_plan,
    apply_progression_policy,
    derive_training_state,
    evaluate_plan,
    generate_plan,
)


def read(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


DB = Database.load(ROOT / "free-exercise-db-plusplus.json")
REL = RelationshipRegistry.load(db=DB)


def main() -> None:
    base = ROOT / "fixtures" / "cross-language"

    plan = read("examples/plans/basic-upper-lower.json")
    profile = read("examples/plan-evaluation/profile-golden.json")
    target = read("examples/targets/example-hypertrophy.json")
    evaluation_input = {"plan": plan, "profile": profile, "target": target,
                        "relationships": REL.document}
    write(base / "evaluation/input.json", evaluation_input)
    write(base / "evaluation/expected.json",
          evaluate_plan(plan, DB, profile, target, REL))
    write(base / "evaluation/metadata.json", {
        "expectedOperation": "evaluate_plan", "oracle": "python",
        "dbSchemaVersion": DB.metadata.get("schemaVersion"),
        "relationshipSchemaVersion": REL.document.get("schemaVersion"),
    })

    history_doc = read("fixtures/cross-language/intent/history-aware/history.json")
    history_input = {"subjectId": history_doc["subjectId"],
                     "plans": [history_doc["plans"][0]],
                     "workouts": history_doc["workouts"],
                     "targets": [],
                     "planActivations": history_doc["planActivations"],
                     "asOf": "2026-08-27T12:00:00-04:00",
                     "window": "last_28_days", "timezone": "America/New_York",
                     "relationships": REL.document}
    history = TrainingHistory(history_input["subjectId"], history_input["plans"],
                              history_input["workouts"], history_input["targets"],
                              history_input["planActivations"])
    write(base / "history/input.json", history_input)
    write(base / "history/expected.json", derive_training_state(
        history, DB, as_of=history_input["asOf"], window=history_input["window"],
        timezone=history_input["timezone"], relationships=REL))
    write(base / "history/metadata.json", {
        "expectedOperation": "derive_training_state", "oracle": "python",
        "timezone": history_input["timezone"], "asOf": history_input["asOf"],
    })

    rx = {"prescriptionId": "bench-rx", "exerciseId": "Barbell_Bench_Press_-_Medium_Grip",
          "sets": 2, "reps": {"min": 6, "target": 8, "max": 10},
          "load": {"value": 80, "unit": "kg"}, "effort": {"rir": {"target": 2}}}
    progression_cases = [
        {"id": "top-reps-effort-ok", "prescription": rx, "state": {"planId": "p", "revisionId": "r", "lastActual": {"sets": [{"completed": True, "reps": 10, "rir": 2}, {"completed": True, "reps": 10, "rir": 2}]}, "planContext": {"planId": "p", "revisionId": "r"}}},
        {"id": "reps-below-top", "prescription": rx, "state": {"planId": "p", "revisionId": "r", "lastActual": {"sets": [{"completed": True, "reps": 8, "rir": 2}, {"completed": True, "reps": 9, "rir": 2}]}, "planContext": {"planId": "p", "revisionId": "r"}}},
        {"id": "incomplete-workout", "prescription": rx, "state": {"planId": "p", "revisionId": "r", "lastActual": {"sets": [{"completed": True, "reps": 10, "rir": 2}]}, "planContext": {"planId": "p", "revisionId": "r"}}},
        {"id": "effort-too-high", "prescription": rx, "state": {"planId": "p", "revisionId": "r", "lastActual": {"sets": [{"completed": True, "reps": 10, "rir": 1}, {"completed": True, "reps": 10, "rir": 2}]}, "planContext": {"planId": "p", "revisionId": "r"}}},
    ]
    progression_input = {"policy": "double-progression-v1", "parameters": {"loadIncrement": {"value": 2.5, "unit": "kg"}}, "cases": progression_cases}
    write(base / "progression/input.json", progression_input)
    write(base / "progression/expected.json", {case["id"]: apply_progression_policy(
        progression_input["policy"], case["prescription"], case["state"],
        parameters=progression_input["parameters"]) for case in progression_cases})
    write(base / "progression/metadata.json", {"expectedOperation": "apply_progression_policy", "oracle": "python"})

    gen_profile = read("examples/plan-generation/full-body-profile.json")
    gen_target = read("examples/plan-generation/full-body-target.json")
    generation_input = {"profile": gen_profile, "target": gen_target,
                        "policy": "full-body-general-v1", "relationships": REL.document,
                        "requiredExerciseIds": ["Barbell_Bench_Press_-_Medium_Grip"],
                        "lockedExerciseIds": [], "additionalExclusions": []}
    generated = generate_plan(gen_profile, gen_target, DB,
                              policy=generation_input["policy"], relationships=REL,
                              requiredExerciseIds=generation_input["requiredExerciseIds"])
    write(base / "generation/input.json", generation_input)
    write(base / "generation/expected.json", generated)
    write(base / "generation/metadata.json", {"expectedOperation": "generate_plan", "oracle": "python"})

    adaptation_plan = {"schemaVersion": "0.1.0", "planId": "adaptive-plan",
                       "revisionId": "r1", "name": "Adaptive fixture",
                       "cycle": {"lengthDays": 7}, "sessions": [{
                           "planSessionId": "adaptive-session", "dayOffset": 0,
                           "exercises": [{"prescriptionId": "adaptive-bench",
                                          "exerciseId": "Barbell_Bench_Press_-_Medium_Grip",
                                          "order": 1, "sets": 2,
                                          "reps": {"min": 6, "target": 8, "max": 10},
                                          "load": {"value": 80, "unit": "kg"},
                                          "effort": {"rir": {"target": 2}}}]}]}
    adaptation_profile = {"schemaVersion": "0.1.0", "profileId": "adaptive-profile",
                          "availability": {"cycleLengthDays": 7,
                                            "sessionsPerCycle": {"target": 1}},
                          "equipment": ["barbell", "dumbbell", "body only"],
                          "constraints": {"excludedExerciseIds": [], "excludedFamilyIds": []}}
    adaptation_target = {"schemaVersion": "0.1.0", "targetId": "adaptive-target",
                         "periodDays": 7, "muscles": {"chest": {"min": 1, "target": 2, "max": 4}}}
    adaptation_workout = {"schemaVersion": "0.3.0", "sessionId": "adaptive-workout",
                          "startTime": "2026-08-24T12:00:00Z",
                          "planReference": {"planId": "adaptive-plan", "revisionId": "r1",
                                             "planSessionId": "adaptive-session"},
                          "exercises": [{"exerciseId": "Barbell_Bench_Press_-_Medium_Grip",
                                          "exercisePrescriptionId": "adaptive-bench",
                                          "sets": [{"setNumber": 1, "setType": "working", "completed": True, "reps": 10, "rir": 2},
                                                    {"setNumber": 2, "setType": "working", "completed": True, "reps": 10, "rir": 2}]}]}
    adaptation_history_doc = {"subjectId": "adaptive-subject", "plans": [adaptation_plan],
                              "workouts": [dict(adaptation_workout,
                                                sessionId="adaptive-workout-1",
                                                startTime="2026-08-23T12:00:00Z"),
                                           adaptation_workout], "targets": [adaptation_target],
                              "planActivations": [{"planId": adaptation_plan["planId"], "revisionId": adaptation_plan["revisionId"], "effectiveFrom": "2026-08-01T00:00:00Z"}]}
    adaptation_input = {"profile": adaptation_profile, "target": adaptation_target, "currentPlan": adaptation_plan,
                        "history": adaptation_history_doc, "asOf": "2026-08-27T12:00:00Z",
                        "relationships": REL.document, "policy": "general-adaptive-v1"}
    adaptation_history = TrainingHistory(adaptation_history_doc["subjectId"], adaptation_history_doc["plans"], adaptation_history_doc["workouts"], [adaptation_target], adaptation_history_doc["planActivations"])
    adapted = adapt_plan(adaptation_profile, adaptation_target, adaptation_plan, adaptation_history, DB,
                         policy=adaptation_input["policy"], relationships=REL,
                         options={"asOf": adaptation_input["asOf"]})
    write(base / "adaptation/input.json", adaptation_input)
    write(base / "adaptation/expected.json", adapted)
    write(base / "adaptation/metadata.json", {"expectedOperation": "adapt_plan", "oracle": "python"})


if __name__ == "__main__":
    main()
