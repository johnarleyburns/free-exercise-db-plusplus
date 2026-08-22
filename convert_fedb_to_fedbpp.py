#!/usr/bin/env python3
"""
Convert yuhonas/free-exercise-db combined exercises JSON into Free Exercise DB++.

v0.1 goals:
- deterministic and reviewable;
- preserve original source record;
- distinguish direct, indirect, and stabilizer roles;
- flag uncertain fallback classifications;
- validate against JSON Schema optionally.

This is deliberately conservative. A low-confidence mapping is preferable to
silently pretending that a complex exercise has been biomechanically resolved.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"
CONVERTER_VERSION = "0.2.0"
UPSTREAM_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"

MUSCLES = [
    "abdominals","abductors","adductors","biceps","calves","chest",
    "forearms","glutes","hamstrings","lats","lower_back","middle_back",
    "neck","quadriceps","shoulders","traps","triceps",
    "tibialis","rotator_cuff","hip_flexors",
]

SET_CREDITS = {"direct": 1.0, "indirect": 0.5, "stabilizer": 0.0}

LABEL_MAP = {
    "lower back": "lower_back",
    "middle back": "middle_back",
}

NON_VOLUME_CATEGORIES = {"stretching", "cardio", "plyometrics"}

PATTERNS: dict[str, dict[str, list[str]]] = {
    "horizontal_press": {
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
    },
    "incline_press": {
        "direct": ["chest", "shoulders"],
        "indirect": ["triceps"],
        "stabilizers": [],
    },
    "decline_press": {
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
    },
    "vertical_press": {
        "direct": ["shoulders"],
        "indirect": ["triceps"],
        "stabilizers": ["abdominals"],
    },
    "horizontal_pull": {
        "direct": ["middle_back", "lats"],
        "indirect": ["biceps", "shoulders"],
        "stabilizers": ["forearms"],
    },
    "vertical_pull": {
        "direct": ["lats"],
        "indirect": ["biceps", "middle_back"],
        "stabilizers": ["forearms"],
    },
    "shrug": {
        "direct": ["traps"],
        "indirect": [],
        "stabilizers": ["forearms"],
    },
    "reverse_fly": {
        "direct": ["shoulders", "middle_back"],
        "indirect": ["traps"],
        "stabilizers": [],
    },
    "shoulder_abduction": {
        "direct": ["shoulders"],
        "indirect": ["traps"],
        "stabilizers": [],
    },
    "shoulder_external_rotation": {
        "direct": ["rotator_cuff"],
        "indirect": [],
        "stabilizers": [],
    },
    "elbow_flexion": {
        "direct": ["biceps"],
        "indirect": ["forearms"],
        "stabilizers": [],
    },
    "elbow_flexion_brachioradialis_bias": {
        "direct": ["biceps", "forearms"],
        "indirect": [],
        "stabilizers": [],
    },
    "elbow_extension": {
        "direct": ["triceps"],
        "indirect": [],
        "stabilizers": [],
    },
    "wrist_flexion": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "wrist_extension": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "squat": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["lower_back", "hamstrings", "calves"],
    },
    "squat_quad_bias": {
        "direct": ["quadriceps"],
        "indirect": ["glutes", "adductors"],
        "stabilizers": ["lower_back"],
    },
    "lunge": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["hamstrings", "calves"],
    },
    "step_up": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["calves"],
    },
    "knee_extension": {
        "direct": ["quadriceps"], "indirect": [], "stabilizers": []
    },
    "knee_flexion": {
        "direct": ["hamstrings"], "indirect": ["calves"], "stabilizers": []
    },
    "hip_hinge": {
        "direct": ["hamstrings", "glutes"],
        "indirect": [],
        "stabilizers": ["lower_back", "forearms"],
    },
    "hip_extension": {
        "direct": ["glutes"],
        "indirect": ["hamstrings"],
        "stabilizers": ["lower_back"],
    },
    "hip_abduction": {
        "direct": ["abductors"], "indirect": ["glutes"], "stabilizers": []
    },
    "hip_adduction": {
        "direct": ["adductors"], "indirect": [], "stabilizers": []
    },
    "plantar_flexion_straight_knee": {
        "direct": ["calves"], "indirect": [], "stabilizers": []
    },
    "leg_press": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": [],
    },
    "conventional_deadlift": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps"],
        "stabilizers": ["lower_back", "traps", "forearms", "lats"],
    },
    "sumo_deadlift": {
        "direct": ["glutes", "quadriceps", "adductors"],
        "indirect": ["hamstrings"],
        "stabilizers": ["lower_back", "traps", "forearms"],
    },
    "chest_fly": {
        "direct": ["chest"], "indirect": [], "stabilizers": ["shoulders"]
    },
    "pullover": {
        "direct": ["lats"], "indirect": ["chest"], "stabilizers": ["triceps"]
    },
    "upright_row": {
        "direct": ["shoulders", "traps"],
        "indirect": ["biceps"],
        "stabilizers": ["forearms"],
    },
    "face_pull": {
        "direct": ["shoulders", "middle_back"],
        "indirect": ["traps", "biceps"],
        "stabilizers": ["forearms"],
    },
    "shoulder_flexion": {
        "direct": ["shoulders"], "indirect": [], "stabilizers": []
    },
    "shoulder_internal_rotation": {
        "direct": ["rotator_cuff"], "indirect": [], "stabilizers": []
    },
    "hip_flexion": {
        "direct": ["hip_flexors"], "indirect": ["abdominals"], "stabilizers": []
    },
    "plantar_flexion_bent_knee": {
        "direct": ["calves"], "indirect": [], "stabilizers": []
    },
    "dorsiflexion": {
        "direct": ["tibialis"], "indirect": [], "stabilizers": []
    },
    "anti_extension": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": ["shoulders"]
    },
    "lateral_flexion": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "farmer_carry": {
        "direct": ["forearms", "traps"],
        "indirect": [],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "loaded_carry": {
        "direct": ["forearms"], "indirect": ["traps"],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "sled_push": {
        "direct": ["quadriceps", "glutes"], "indirect": ["calves"],
        "stabilizers": ["abdominals"],
    },
    "sled_pull": {
        "direct": ["quadriceps", "glutes"], "indirect": ["hamstrings", "calves"],
        "stabilizers": ["forearms"],
    },
    "kettlebell_swing": {
        "direct": ["glutes", "hamstrings"], "indirect": [],
        "stabilizers": ["lower_back", "forearms"],
    },
    "trunk_flexion": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "trunk_extension": {
        "direct": ["lower_back"],
        "indirect": ["glutes", "hamstrings"],
        "stabilizers": [],
    },
    "trunk_rotation": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "neck_flexion": {
        "direct": ["neck"], "indirect": [], "stabilizers": []
    },
    "neck_extension": {
        "direct": ["neck"], "indirect": [], "stabilizers": []
    },
}

# Exact overrides are the highest-precedence semantic layer.
# This initial list is intentionally small and should grow through review.
OVERRIDES: dict[str, dict[str, Any]] = {
    "Barbell_Bench_Press_-_Medium_Grip": {
        "patterns": ["horizontal_press"],
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Barbell_Full_Squat": {
        "patterns": ["squat"],
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["hamstrings", "lower_back", "calves"],
        "confidence": "high",
        "reviewReasons": [],
    },
}

def normalize_muscle(label: str) -> str:
    return LABEL_MAP.get(label, label.replace(" ", "_"))

def normalized_list(labels: list[str]) -> list[str]:
    return dedupe([normalize_muscle(x) for x in labels])

def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))

def infer_pattern(exercise: dict[str, Any]) -> str | None:
    name = exercise.get("name", "").lower()
    primary = set(exercise.get("primaryMuscles", []))

    # Highly specific rules before generic ones.
    if "incline" in name and ("press" in name or "push-up" in name or "push up" in name):
        return "incline_press"
    if "decline" in name and ("press" in name or "push-up" in name or "push up" in name):
        return "decline_press"
    if "bench press" in name or "chest press" in name or "push-up" in name or "push up" in name:
        return "horizontal_press"
    if ("military press" in name or "overhead press" in name or "shoulder press" in name
            or "arnold press" in name):
        return "vertical_press"
    if "pull-up" in name or "pull up" in name or "chin-up" in name or "chin up" in name or "pulldown" in name:
        return "vertical_pull"
    if "face pull" in name:
        return "face_pull"
    if "upright row" in name:
        return "upright_row"
    if "row" in name:
        return "horizontal_pull"
    if "shrug" in name:
        return "shrug"
    if "pullover" in name or "pull-over" in name:
        return "pullover"
    if any(x in name for x in ["pec deck", "butterfly", "chest fly", "chest flye",
                               "dumbbell fly", "dumbbell flye", "cable crossover"]):
        return "chest_fly"
    if "reverse fly" in name or "rear delt" in name:
        return "reverse_fly"
    if "lateral raise" in name or "side lateral" in name:
        return "shoulder_abduction"
    if "front raise" in name:
        return "shoulder_flexion"
    if "external rotation" in name:
        return "shoulder_external_rotation"
    if "internal rotation" in name:
        return "shoulder_internal_rotation"
    if "hammer curl" in name or "reverse curl" in name:
        return "elbow_flexion_brachioradialis_bias"
    if "curl" in name and ("leg curl" not in name):
        return "elbow_flexion"
    if any(x in name for x in ["triceps extension", "tricep extension", "pushdown", "pressdown", "skull crusher"]):
        return "elbow_extension"
    if "wrist curl" in name:
        return "wrist_flexion"
    if "reverse wrist curl" in name or "wrist extension" in name:
        return "wrist_extension"
    if "leg press" in name:
        return "leg_press"
    if "leg extension" in name:
        return "knee_extension"
    if "leg curl" in name:
        return "knee_flexion"
    if "step-up" in name or "step up" in name:
        return "step_up"
    if any(x in name for x in ["lunge", "split squat"]):
        return "lunge"
    if "front squat" in name or "hack squat" in name:
        return "squat_quad_bias"
    if "squat" in name:
        return "squat"
    if "sumo deadlift" in name:
        return "sumo_deadlift"
    if any(x in name for x in ["romanian deadlift", "stiff-legged deadlift", "stiff legged deadlift",
                               "stiff-leg deadlift", "good morning"]):
        return "hip_hinge"
    if "deadlift" in name:
        return "conventional_deadlift"
    if any(x in name for x in ["hip thrust", "glute bridge", "glute kickback",
                                 "glute kick back", "pull-through", "pull through"]):
        return "hip_extension"
    if any(x in name for x in ["hip flexion", "knee raise", "leg raise"]):
        return "hip_flexion"
    if "abduction" in name:
        return "hip_abduction"
    if "adduction" in name:
        return "hip_adduction"
    if "seated calf" in name or "seated toe raise" in name:
        return "plantar_flexion_bent_knee"
    if "calf raise" in name or "calf press" in name or "toe raise" in name:
        return "plantar_flexion_straight_knee"
    if "tibialis raise" in name or "dorsiflexion" in name:
        return "dorsiflexion"
    if any(x in name for x in ["ab wheel", "ab roller", "rollout", "roll-out"]):
        return "anti_extension"
    if "side bend" in name or "side plank" in name:
        return "lateral_flexion"
    if any(x in name for x in ["crunch", "sit-up", "sit up"]):
        return "trunk_flexion"
    if "plank" in name:
        return "anti_extension"
    if "back extension" in name or "hyperextension" in name:
        return "trunk_extension"
    if "russian twist" in name or "wood chop" in name or "woodchop" in name or "torso rotation" in name:
        return "trunk_rotation"
    if "farmer" in name and "walk" in name:
        return "farmer_carry"
    if exercise.get("category") == "strongman" and ("carry" in name or "walk" in name):
        return "loaded_carry"
    if "sled push" in name or "prowler" in name:
        return "sled_push"
    if "sled" in name and ("pull" in name or "drag" in name):
        return "sled_pull"
    if "kettlebell swing" in name:
        return "kettlebell_swing"

    # A small muscle-informed assist for obvious isolation records.
    if exercise.get("mechanic") == "isolation":
        if primary == {"quadriceps"}:
            return "knee_extension"
        if primary == {"hamstrings"}:
            return "knee_flexion"
        if primary == {"biceps"}:
            return "elbow_flexion"
        if primary == {"triceps"}:
            return "elbow_extension"
        if primary == {"calves"}:
            return "plantar_flexion_straight_knee"
        if primary == {"abdominals"}:
            return "trunk_flexion"
        if primary == {"adductors"}:
            return "hip_adduction"
        if primary == {"abductors"}:
            return "hip_abduction"

    return None

def roles_from_pattern(pattern: str) -> tuple[list[str], list[str], list[str]]:
    rule = PATTERNS[pattern]
    return (
        list(rule["direct"]),
        list(rule["indirect"]),
        list(rule["stabilizers"]),
    )

def remove_role_overlap(direct: list[str], indirect: list[str], stabilizers: list[str]):
    direct = dedupe(direct)
    indirect = [x for x in dedupe(indirect) if x not in direct]
    stabilizers = [
        x for x in dedupe(stabilizers)
        if x not in direct and x not in indirect
    ]
    return direct, indirect, stabilizers

def annotate(exercise: dict[str, Any]) -> dict[str, Any]:
    category = exercise.get("category")
    eligible = category not in NON_VOLUME_CATEGORIES

    if not eligible:
        return {
            "patterns": [],
            "direct": [],
            "indirect": [],
            "stabilizers": [],
            "volumeEligible": False,
            "confidence": "high",
            "reviewReasons": [f"non_volume_category:{category}"],
        }

    exercise_id = exercise["id"]
    if exercise_id in OVERRIDES:
        ann = copy.deepcopy(OVERRIDES[exercise_id])
        ann["volumeEligible"] = True
        return ann

    pattern = infer_pattern(exercise)
    if pattern is not None:
        direct, indirect, stabilizers = roles_from_pattern(pattern)
        direct, indirect, stabilizers = remove_role_overlap(direct, indirect, stabilizers)
        return {
            "patterns": [pattern],
            "direct": direct,
            "indirect": indirect,
            "stabilizers": stabilizers,
            "volumeEligible": True,
            "confidence": "high" if exercise.get("mechanic") == "isolation" else "medium",
            "reviewReasons": [] if exercise.get("mechanic") == "isolation"
                else ["rule_based_compound_mapping"],
        }

    primary = normalized_list(exercise.get("primaryMuscles", []))
    secondary = normalized_list(exercise.get("secondaryMuscles", []))
    direct, indirect, stabilizers = remove_role_overlap(primary, secondary, [])

    if exercise.get("mechanic") == "isolation":
        confidence = "medium"
        reasons = ["isolation_primary_secondary_fallback"]
    else:
        confidence = "low"
        reasons = ["compound_fallback_requires_review"]

    # If the upstream includes a muscle outside our current ontology, preserve
    # source data but omit that label from annotations and flag it.
    unknown = [m for m in direct + indirect if m not in MUSCLES]
    if unknown:
        direct = [m for m in direct if m in MUSCLES]
        indirect = [m for m in indirect if m in MUSCLES]
        reasons.append("unknown_upstream_muscle:" + ",".join(sorted(set(unknown))))
        confidence = "low"

    return {
        "patterns": [],
        "direct": direct,
        "indirect": indirect,
        "stabilizers": stabilizers,
        "volumeEligible": True,
        "confidence": confidence,
        "reviewReasons": reasons,
    }

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def convert(source_path: Path, completeness: str) -> dict[str, Any]:
    with source_path.open("r", encoding="utf-8") as f:
        source = json.load(f)

    if not isinstance(source, list):
        raise ValueError("Expected upstream combined JSON to be an array of exercise objects")

    exercises: dict[str, Any] = {}
    for item in source:
        exercise_id = item["id"]
        exercises[exercise_id] = {
            "exerciseId": exercise_id,
            "annotation": annotate(item),
            "source": item,
        }

    return {
        "metadata": {
            "schemaVersion": SCHEMA_VERSION,
            "converterVersion": CONVERTER_VERSION,
            "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "upstream": {
                "project": "yuhonas/free-exercise-db",
                "sourceUrl": UPSTREAM_URL,
                "sha256": sha256_file(source_path),
            },
            "setCredits": SET_CREDITS,
            "muscleOntology": MUSCLES,
            "sourceExerciseCount": len(source),
            "outputExerciseCount": len(exercises),
            "completeness": completeness,
        },
        "exercises": exercises,
    }

def validate(data: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as e:
        raise SystemExit(
            "Schema validation requested but jsonschema is not installed. "
            "Run: python3 -m pip install jsonschema"
        ) from e

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Upstream combined exercises.json")
    parser.add_argument("output", type=Path, help="Output FEDB++ JSON")
    parser.add_argument("--schema", type=Path, help="Optional DB++ JSON Schema to validate output")
    parser.add_argument(
        "--completeness",
        choices=["full", "fixture", "partial"],
        default="full",
        help="Provenance marker written to output metadata",
    )
    args = parser.parse_args()

    data = convert(args.source, args.completeness)

    if args.schema:
        validate(data, args.schema)

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"Wrote {len(data['exercises'])} exercises to {args.output} "
        f"(completeness={args.completeness})"
    )

if __name__ == "__main__":
    main()
