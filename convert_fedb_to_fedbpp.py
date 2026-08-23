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

SCHEMA_VERSION = "0.2.0"
CONVERTER_VERSION = "0.4.1"
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
    "horizontal_press_triceps_bias": {
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
    },
    "dip_chest_bias": {
        "direct": ["chest", "triceps"],
        "indirect": ["shoulders"],
        "stabilizers": [],
    },
    "dip_triceps_bias": {
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
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
    "glute_ham_raise": {
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
    },
    "rack_pull": {
        "direct": ["glutes", "hamstrings"],
        "indirect": [],
        "stabilizers": ["lower_back", "traps", "forearms", "lats"],
    },
    "anti_rotation": {
        "direct": ["abdominals"],
        "indirect": [],
        "stabilizers": [],
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
    "olympic_clean_pull": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "olympic_clean": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals", "shoulders"],
    },
    "olympic_snatch_pull": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "olympic_snatch": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["shoulders", "triceps", "lower_back", "forearms", "abdominals"],
    },
    "olympic_jerk": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "olympic_clean_and_jerk": {
        "direct": ["quadriceps", "glutes", "traps", "shoulders", "triceps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "snatch_balance": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["shoulders", "triceps"],
        "stabilizers": ["traps", "abdominals"],
    },
    "push_press": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "kettlebell_clean": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "kettlebell_snatch": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps", "traps", "shoulders"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "kettlebell_jerk": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["forearms", "abdominals", "traps"],
    },
    "kettlebell_windmill": {
        "direct": ["abdominals"],
        "indirect": ["glutes", "hamstrings"],
        "stabilizers": ["shoulders", "triceps"],
    },
    "kettlebell_sumo_high_pull": {
        "direct": ["glutes", "quadriceps", "traps", "shoulders"],
        "indirect": ["hamstrings", "adductors", "biceps"],
        "stabilizers": ["forearms", "abdominals"],
    },
    "thruster": {
        "direct": ["quadriceps", "glutes", "shoulders", "triceps"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "muscle_up": {
        "direct": ["lats", "chest", "triceps"],
        "indirect": ["biceps", "shoulders", "middle_back"],
        "stabilizers": ["forearms", "abdominals"],
    },
    "rope_climb": {
        "direct": ["lats", "biceps", "forearms"],
        "indirect": ["middle_back"],
        "stabilizers": ["abdominals"],
    },
    "atlas_stone_load": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["biceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "loaded_object_load": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["biceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "tire_flip": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["chest", "triceps", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "strongman_overhead": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["traps", "calves"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "strongman_carry": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["traps", "biceps"],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "power_stairs": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "abdominals"],
    },
    "battle_ropes": {
        "direct": ["shoulders"],
        "indirect": ["forearms", "chest"],
        "stabilizers": ["abdominals"],
    },
    "bent_press": {
        "direct": ["abdominals", "shoulders"],
        "indirect": ["glutes", "hamstrings", "triceps"],
        "stabilizers": ["lower_back", "quadriceps"],
    },
    "kettlebell_figure8": {
        "direct": ["abdominals"],
        "indirect": ["glutes", "hamstrings", "shoulders"],
        "stabilizers": ["forearms", "lower_back"],
    },
    "kettlebell_pirate_ships": {
        "direct": ["shoulders", "abdominals"],
        "indirect": ["lats"],
        "stabilizers": ["forearms", "lower_back"],
    },
    "drag_with_press": {
        "direct": ["quadriceps", "glutes", "chest", "triceps"],
        "indirect": ["calves", "hamstrings", "shoulders"],
        "stabilizers": ["abdominals", "forearms"],
    },
    "spider_crawl": {
        "direct": ["abdominals"],
        "indirect": ["shoulders", "chest", "triceps"],
        "stabilizers": ["glutes"],
    },
    "medicine_ball_slam": {
        "direct": ["abdominals", "lats"],
        "indirect": ["shoulders"],
        "stabilizers": ["glutes", "quadriceps"],
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

    "Pullups": {
        "patterns": ["vertical_pull"],
        "direct": ["lats"],
        "indirect": ["biceps", "middle_back"],
        "stabilizers": ["forearms"],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Dips_-_Chest_Version": {
        "patterns": ["dip_chest_bias"],
        "direct": ["chest", "triceps"],
        "indirect": ["shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Dips_-_Triceps_Version": {
        "patterns": ["dip_triceps_bias"],
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Glute_Ham_Raise": {
        "patterns": ["glute_ham_raise"],
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Natural_Glute_Ham_Raise": {
        "patterns": ["glute_ham_raise"],
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
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
    # v0.4.1: resolve the remaining known named movements.
    if name == "alternating hang clean":
        return "olympic_clean"
    if name == "dumbbell clean":
        return "olympic_clean"
    if name == "bottoms-up clean from the hang position":
        return "kettlebell_clean"
    if name == "anti-gravity press":
        return "vertical_press"
    if name == "bent press":
        return "bent_press"
    if name == "forward drag with press":
        return "drag_with_press"
    if name in {"kettlebell figure 8", "kettlebell pass between the legs"}:
        return "kettlebell_figure8"
    if name == "kettlebell pirate ships":
        return "kettlebell_pirate_ships"
    if name == "landmine 180's":
        return "trunk_rotation"
    if name == "one-arm kettlebell para press":
        return "vertical_press"
    if name == "one-arm medicine ball slam":
        return "medicine_ball_slam"
    if name == "spider crawl":
        return "spider_crawl"

    # v0.4: Olympic weightlifting and related derivatives.
    if name == "clean and jerk":
        return "olympic_clean_and_jerk"
    if name in {"clean pull"}:
        return "olympic_clean_pull"
    if name in {"snatch pull"}:
        return "olympic_snatch_pull"
    if "snatch balance" in name:
        return "snatch_balance"
    if name in {"clean", "power clean", "hang clean", "split clean", "clean from blocks",
                "power clean from blocks", "hang clean - below the knees",
                "smith machine hang power clean"}:
        return "olympic_clean"
    if name in {"snatch", "power snatch", "hang snatch", "split snatch", "muscle snatch",
                "snatch from blocks", "power snatch from blocks", "hang snatch - below knees"}:
        return "olympic_snatch"
    if name in {"jerk balance", "power jerk", "split jerk"}:
        return "olympic_jerk"
    if name == "clean and press":
        return "olympic_clean_and_jerk"

    # Kettlebell ballistic families.
    if "kettlebell" in name and "clean and jerk" in name:
        return "olympic_clean_and_jerk"
    if "kettlebell" in name and "push press" in name:
        return "push_press"
    if "kettlebell" in name and ("jerk" in name):
        return "kettlebell_jerk"
    if "kettlebell" in name and "snatch" in name:
        return "kettlebell_snatch"
    if "kettlebell" in name and ("clean" in name):
        return "kettlebell_clean"
    if "kettlebell" in name and "windmill" in name:
        return "kettlebell_windmill"
    if "kettlebell" in name and "sumo high pull" in name:
        return "kettlebell_sumo_high_pull"
    if "kettlebell" in name and "thruster" in name:
        return "thruster"

    # Strongman / loaded-object families.
    if "atlas stone" in name:
        return "atlas_stone_load"
    if any(x in name for x in ["keg load", "sandbag load"]):
        return "loaded_object_load"
    if "tire flip" in name:
        return "tire_flip"
    if any(x in name for x in ["log lift", "circus bell", "rack delivery"]):
        return "strongman_overhead"
    if "conan" in name and "wheel" in name:
        return "strongman_carry"
    if "power stairs" in name:
        return "power_stairs"

    # Gymnastic / climbing / integrated.
    if "muscle up" in name:
        return "muscle_up"
    if "rope climb" in name:
        return "rope_climb"
    if "battling ropes" in name:
        return "battle_ropes"

    # v0.3.2 exact conventional-name cleanup.
    if name == "machine shoulder (military) press":
        return "vertical_press"
    if name in {"hip extension with bands", "hip lift with band", "physioball hip bridge"}:
        return "hip_extension"
    if name == "cuban press":
        return "shoulder_external_rotation"
    if name in {"air bike", "bottoms up", "otis-up"}:
        return "trunk_flexion"
    if name in {"plate twist", "standing cable lift", "cable judo flip"}:
        return "trunk_rotation"
    if name == "flutter kicks":
        return "hip_flexion"
    if name == "dumbbell raise":
        return "shoulder_flexion"
    if name == "barbell incline shoulder raise":
        return "shoulder_flexion"
    if name == "neck press":
        return "horizontal_press"
    if name in {"push press", "push press - behind the neck"}:
        return "push_press"
    if name in {"landmine linear jammer", "single-arm linear jammer"}:
        return "push_press"
    if "incline" in name and ("press" in name or "push-up" in name or "push up" in name or "bench" in name):
        return "incline_press"
    if "decline" in name and ("press" in name or "push-up" in name or "push up" in name):
        return "decline_press"
    if any(x in name for x in ["floor press", "board press", "pin press", "chain press"]):
        return "horizontal_press_triceps_bias"
    if any(x in name for x in ["close-grip dumbbell press", "close grip dumbbell press",
                               "close-grip ez-bar press", "close grip ez-bar press",
                               "jm press"]):
        return "horizontal_press_triceps_bias"
    if ("bench press" in name or "chest press" in name or "push-up" in name or "push up" in name
            or "pushups" in name or "floor press" in name):
        return "horizontal_press"
    if ("military press" in name or "overhead press" in name or "shoulder press" in name
            or "arnold press" in name or "arnold dumbbell press" in name
            or "seated dumbbell press" in name or "standing dumbbell press" in name
            or "kettlebell press" in name or "bradford" in name
            or "machine shoulder military press" in name
            or "standing alternating dumbbell press" in name
            or "kettlebell seated press" in name or "kettlebell seesaw press" in name
            or "see-saw press" in name or "seesaw press" in name
            or "press behind neck" in name or "press behind the neck" in name
            or "palms-in dumbbell press" in name or "palm-in one-arm dumbbell press" in name):
        return "vertical_press"
    if any(x in name for x in ["dips - chest version", "parallel bar dip", "ring dips"]):
        return "dip_chest_bias"
    if any(x in name for x in ["dips - triceps version", "bench dips", "bench dip",
                               "weighted bench dip", "dip machine"]):
        return "dip_triceps_bias"
    if ("pull-up" in name or "pull up" in name or "pullup" in name or "pullups" in name
            or "chin-up" in name or "chin up" in name or "chins" in name
            or "mixed grip chin" in name or "pulldown" in name or "v-bar pullup" in name):
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
    if "svend press" in name:
        return "horizontal_press"
    if any(x in name for x in ["pec deck", "butterfly", "chest fly", "chest flye",
                               "dumbbell fly", "dumbbell flye", "cable crossover",
                               "cross over - with bands", "around the worlds"]):
        return "chest_fly"
    if "reverse fly" in name or "back fly" in name or "rear delt" in name:
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
    if "reverse wrist curl" in name or "wrist extension" in name:
        return "wrist_extension"
    if "wrist curl" in name:
        return "wrist_flexion"
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
    if "rack pull" in name:
        return "rack_pull"
    if "sumo deadlift" in name:
        return "sumo_deadlift"
    if any(x in name for x in ["romanian deadlift", "stiff-legged deadlift", "stiff legged deadlift",
                               "stiff-leg deadlift", "wide stance stiff legs", "good morning"]):
        return "hip_hinge"
    if "deadlift" in name:
        return "conventional_deadlift"
    if any(x in name for x in ["hip thrust", "glute bridge", "glute kickback",
                                 "glute kick back", "pull-through", "pull through"]):
        return "hip_extension"
    if any(x in name for x in ["hip flexion", "knee raise", "leg raise"]):
        return "hip_flexion"
    if "monster walk" in name:
        return "hip_abduction"
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
    if "pallof press" in name:
        return "anti_rotation"
    if any(x in name for x in ["side bridge", "side jackknife"]):
        return "lateral_flexion"
    if any(x in name for x in ["dead bug", "butt-ups", "cocoons", "elbow to knee",
                               "leg pull-in", "leg pull in", "hanging pike",
                               "bent-knee hip raise", "bent knee hip raise",
                               "exercise ball pull-in", "exercise ball pull in"]):
        return "trunk_flexion"
    if any(x in name for x in ["crunch", "sit-up", "sit up"]):
        return "trunk_flexion"
    if "plank" in name:
        return "anti_extension"
    if "back extension" in name or "hyperextension" in name:
        return "trunk_extension"
    if ("russian twist" in name or "wood chop" in name or "woodchop" in name
            or "torso rotation" in name or "plate twist" in name
            or "standing cable lift" in name or "london bridges" in name):
        return "trunk_rotation"
    if "farmer" in name and "walk" in name:
        return "farmer_carry"
    if exercise.get("category") == "strongman" and ("carry" in name or "walk" in name):
        return "loaded_carry"
    if "sled push" in name or "prowler" in name:
        return "sled_push"
    if "backward drag" in name:
        return "sled_pull"
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

    # Other named integrated movements kept medium-confidence rather than fallback-low.
    if name in {"iron cross", "isometric wipers"}:
        return "anti_extension"
    if name in {"landmine 180s", "spell caster"}:
        return "trunk_rotation"
    if name == "sled overhead backward walk":
        return "sled_pull"

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


def classify_exercise(exercise: dict[str, Any]) -> dict[str, list[str]]:
    category = (exercise.get("category") or "").lower()
    equipment = (exercise.get("equipment") or "").lower()
    name = (exercise.get("name") or "").lower().strip()

    training = []
    category_map = {
        "strength": "strength",
        "powerlifting": "powerlifting",
        "olympic weightlifting": "olympic_weightlifting",
        "strongman": "strongman",
        "plyometrics": "plyometrics",
        "cardio": "cardio",
        "stretching": "stretching",
    }
    if category in category_map:
        training.append(category_map[category])
    if category in {"powerlifting", "olympic weightlifting", "strongman"}:
        training.insert(0, "strength")

    modalities = []
    equipment_map = {
        "body only": "bodyweight",
        "barbell": "free_weight",
        "dumbbell": "free_weight",
        "e-z curl bar": "free_weight",
        "machine": "machine",
        "cable": "cable",
        "bands": "band",
        "kettlebells": "kettlebell",
        "medicine ball": "medicine_ball",
        "foam roll": "foam_roll",
    }
    if equipment in equipment_map:
        modalities.append(equipment_map[equipment])
    elif equipment:
        modalities.append("other")
    if "kettlebell" in name:
        modalities.append("kettlebell")
    if "sled" in name or "prowler" in name or "drag" in name:
        modalities.append("sled")
    if "rope" in name:
        modalities.append("rope")
    if category == "strongman" and any(x in name for x in ["stone", "keg", "log", "tire", "sandbag", "yoke", "conan"]):
        modalities.append("loaded_object")
    if not modalities:
        modalities = ["other"]

    contexts = ["general_fitness"]
    if category == "powerlifting":
        contexts.append("powerlifting")
    if category == "olympic weightlifting":
        contexts.append("weightlifting")
    if category == "strongman":
        contexts.append("strongman")
    if any(x in name for x in ["kipping muscle up", "muscle up", "thruster", "wall ball", "double under", "toes to bar"]):
        contexts.append("crossfit")
    if any(x in name for x in ["muscle up", "ring dip", "iron cross"]):
        contexts.append("gymnastics")

    competition = []
    if category == "powerlifting":
        if name in {"squat", "barbell full squat"}:
            competition.append("powerlifting_squat")
        if "bench press" in name and all(x not in name for x in ["incline", "decline", "close-grip", "close grip"]):
            competition.append("powerlifting_bench_press")
        if name in {"deadlift", "barbell deadlift"}:
            competition.append("powerlifting_deadlift")
    if category == "olympic weightlifting":
        if name == "snatch":
            competition.append("weightlifting_snatch")
        if name == "clean and jerk":
            competition.append("weightlifting_clean_and_jerk")

    return {
        "trainingTypes": dedupe(training),
        "modalities": dedupe(modalities),
        "sportContexts": dedupe(contexts),
        "competitionMovements": dedupe(competition),
    }

def annotate(exercise: dict[str, Any]) -> dict[str, Any]:
    category = exercise.get("category")
    name = (exercise.get("name") or "").lower().strip()

    # Some upstream "strength" records are not resistance-set exercises for DB++.
    if name in {"wind sprints", "balance board"}:
        return {
            "patterns": [],
            "direct": [],
            "indirect": [],
            "stabilizers": [],
            "volumeEligible": False,
            "confidence": "high",
            "reviewReasons": ["non_volume_named_override"],
        }
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
        complex_patterns = {
            "olympic_clean_pull", "olympic_clean", "olympic_snatch_pull", "olympic_snatch",
            "olympic_jerk", "olympic_clean_and_jerk", "snatch_balance", "push_press",
            "kettlebell_clean", "kettlebell_snatch", "kettlebell_jerk", "kettlebell_windmill",
            "kettlebell_sumo_high_pull", "thruster", "muscle_up", "rope_climb",
            "atlas_stone_load", "loaded_object_load", "tire_flip", "strongman_overhead",
            "strongman_carry", "power_stairs", "battle_ropes", "bent_press",
            "kettlebell_figure8", "kettlebell_pirate_ships", "drag_with_press",
            "spider_crawl", "medicine_ball_slam"
        }
        if exercise.get("mechanic") == "isolation":
            confidence = "high"
            reasons = []
        elif pattern in complex_patterns:
            confidence = "medium"
            reasons = ["reviewed_complex_pattern_rule"]
        else:
            confidence = "medium"
            reasons = ["rule_based_compound_mapping"]
        return {
            "patterns": [pattern],
            "direct": direct,
            "indirect": indirect,
            "stabilizers": stabilizers,
            "volumeEligible": True,
            "confidence": confidence,
            "reviewReasons": reasons,
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
            "classification": classify_exercise(item),
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
