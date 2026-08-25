"""Build the reviewed, deterministic v1.5 relationship artifact."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from .overrides import EXCLUDED_FAMILY_IDS, FAMILY_OVERRIDES

SCHEMA_VERSION = "0.1.0"
RELATIONSHIPS = ("member_of_family", "variation_of", "equipment_variant_of",
                 "grip_variant_of", "stance_variant_of", "angle_variant_of",
                 "laterality_variant_of")
FAMILIES = {
    "bench_press": ("Bench Press", ("bench press",)),
    "squat": ("Squat", ()),
    "deadlift": ("Deadlift", ()),
    "romanian_deadlift": ("Romanian Deadlift", ("RDL",)),
    "row": ("Row", ()),
    "pull_up": ("Pull-Up", ("pullup", "pull up")),
    "chin_up": ("Chin-Up", ("chinup", "chin up")),
    "shoulder_press": ("Shoulder Press", ("overhead press", "military press")),
    "biceps_curl": ("Biceps Curl", ("barbell curl",)),
    "triceps_extension": ("Triceps Extension", ("skull crusher", "pushdown")),
    "leg_press": ("Leg Press", ()),
    "leg_extension": ("Leg Extension", ()),
    "calf_raise": ("Calf Raise", ()),
    "chest_fly": ("Chest Fly", ("flye", "flyes")),
    "hip_thrust": ("Hip Thrust", ()),
    "glute_bridge": ("Glute Bridge", ()),
}

def _text(eid: str, rec: dict[str, Any]) -> str:
    return rec.get("source", {}).get("name", eid).casefold()

def _phrase(text: str, expression: str) -> bool:
    return re.search(rf"(?<![a-z0-9])(?:{expression})(?![a-z0-9])", text) is not None

def _family_for(eid: str, rec: dict[str, Any], *, candidates_only: bool = False) -> Any:
    text = _text(eid, rec)
    if eid in FAMILY_OVERRIDES and not candidates_only:
        return FAMILY_OVERRIDES[eid], "manual_review", "high"
    patterns = set(rec.get("annotation", {}).get("patterns", []))
    category = rec.get("source", {}).get("category")
    resistance = category in {"strength", "powerlifting", "olympic weightlifting", "strongman", "plyometrics"}
    primary_muscles = set(rec.get("source", {}).get("primaryMuscles", ()))
    def excluded(f): return f in EXCLUDED_FAMILY_IDS.get(eid, set())
    tests: list[tuple[str, Callable[[], bool], str]] = [
        ("bench_press", lambda: resistance and _phrase(text, r"bench[ -]+press") and bool(patterns & {"horizontal_press", "incline_press", "decline_press"}) and not excluded("bench_press"), "high"),
        ("romanian_deadlift", lambda: resistance and _phrase(text, r"romanian[ -]+deadlifts?") and not excluded("romanian_deadlift"), "high"),
        ("deadlift", lambda: resistance and _phrase(text, r"deadlifts?") and bool(patterns & {"conventional_deadlift", "sumo_deadlift"}) and not any(word in text for word in ("romanian", "stiff-legged", "stiff legged")) and not excluded("deadlift"), "medium"),
        ("pull_up", lambda: resistance and _phrase(text, r"pull[ -]?ups?") and "vertical_pull" in patterns and not excluded("pull_up"), "high"),
        ("chin_up", lambda: resistance and _phrase(text, r"chins?|chin[ -]?ups?") and "vertical_pull" in patterns and not excluded("chin_up"), "high"),
        ("row", lambda: resistance and _phrase(text, r"rows?") and "horizontal_pull" in patterns and "upright" not in text and not excluded("row"), "medium"),
        ("shoulder_press", lambda: resistance and _phrase(text, r"press(?:es)?") and "vertical_press" in patterns and "push press" not in text and not excluded("shoulder_press"), "medium"),
        ("biceps_curl", lambda: resistance and "biceps" in primary_muscles and _phrase(text, r"curls?") and any(p.startswith("elbow_flexion") for p in patterns) and not any(word in text for word in ("wrist", "finger")) and not excluded("biceps_curl"), "high"),
        ("triceps_extension", lambda: resistance and "triceps" in primary_muscles and "elbow_extension" in patterns and any(_phrase(text, token) for token in (r"triceps?", r"skull[ -]?crushers?", r"pushdowns?")) and not excluded("triceps_extension"), "high"),
        ("leg_press", lambda: resistance and _phrase(text, r"leg[ -]+press") and "calf" not in text and not excluded("leg_press"), "high"),
        ("leg_extension", lambda: resistance and _phrase(text, r"leg[ -]+extensions?") and not excluded("leg_extension"), "high"),
        ("calf_raise", lambda: resistance and "calves" in primary_muscles and _phrase(text, r"calf[ -]+raises?") and not excluded("calf_raise"), "high"),
        ("chest_fly", lambda: resistance and "chest" in primary_muscles and "chest_fly" in patterns and not excluded("chest_fly"), "medium"),
        ("hip_thrust", lambda: resistance and _phrase(text, r"hip[ -]+thrusts?") and not excluded("hip_thrust"), "high"),
        ("glute_bridge", lambda: resistance and _phrase(text, r"glute[ -]+bridges?") and not excluded("glute_bridge"), "high"),
        ("squat", lambda: resistance and _phrase(text, r"squats?") and any(p == "squat" or p.startswith("squat_") for p in patterns) and not excluded("squat"), "medium"),
    ]
    candidates=[(family,confidence) for family,predicate,confidence in tests if predicate()]
    if candidates_only: return candidates
    if candidates:
        family,confidence=candidates[0]; return family,"rule",confidence
    return None, None, None

def _dimensions(eid: str, rec: dict[str, Any]) -> dict[str, str]:
    text = _text(eid, rec)
    source = rec.get("source", {})
    equipment = source.get("equipment")
    dims: dict[str, str] = {}
    if equipment:
        dims["equipment"] = {"body only":"bodyweight", "e-z curl bar":"ez_bar", "kettlebells":"kettlebell"}.get(equipment, equipment.replace(" ", "_"))
    for value, tokens in (("close", ("close-grip", "close grip")), ("wide", ("wide-grip", "wide grip")), ("neutral", ("neutral grip", "palms in", "palms-in", "hammer grip")), ("reverse", ("reverse grip",)), ("mixed", ("mixed grip",)), ("pronated", ("pronated grip",)), ("supinated", ("supinated grip",))):
        if any(t in text for t in tokens): dims["grip"] = value; break
    if "incline" in text or "incline_press" in rec.get("annotation", {}).get("patterns", []): dims["angle"] = "incline"
    elif "decline" in text or "decline_press" in rec.get("annotation", {}).get("patterns", []): dims["angle"] = "decline"
    elif "flat" in text: dims["angle"] = "flat"
    for value, tokens in (("unilateral", ("one-arm", "one arm", "single-arm", "single arm", "one-legged", "one leg")), ("bilateral", ("two-arm", "two arm", "two-dumbbell", "two dumbbell"))):
        if any(t in text for t in tokens): dims["laterality"] = value; break
    if "wide stance" in text or "wide_stance" in eid.casefold(): dims["stance"] = "wide"
    elif "narrow stance" in text or "narrow_stance" in eid.casefold(): dims["stance"] = "narrow"
    elif "sumo" in text: dims["stance"] = "sumo"
    elif "split squat" in text: dims["stance"] = "split"
    if "front" in text and "squat" in text: dims["load_position"] = "front"
    elif "overhead" in text and "squat" in text: dims["load_position"] = "overhead"
    elif "zercher" in text: dims["load_position"] = "zercher"
    elif "goblet" in text: dims["load_position"] = "goblet"
    for value in ("standing", "seated", "lying", "kneeling"):
        if _phrase(text, value): dims["body_position"] = value; break
    if "reverse band" in text: dims["assistance"] = "reverse_band"
    elif "assisted" in text: dims["assistance"] = "assisted"
    if "with chains" in text: dims["resistance_type"] = "chains"
    elif "with bands" in text or "band" in text: dims["resistance_type"] = "bands"
    return dict(sorted(dims.items()))

def build_relationship_document(db: dict[str, Any], *, generated_from: str | None = None) -> dict[str, Any]:
    exercises = db["exercises"]
    families = {k: {"familyId": k, "name": v[0], "aliases": list(v[1])} for k, v in sorted(FAMILIES.items())}
    assignments = []
    for eid in sorted(exercises):
        family, source_kind, confidence = _family_for(eid, exercises[eid])
        if family is None: continue
        assignments.append({"sourceExerciseId": eid, "familyId": family, "relationship": "member_of_family", "dimensions": _dimensions(eid, exercises[eid]), "confidence": confidence, "provenance": [{"type": source_kind, "source": "src/relationships/overrides.py" if source_kind == "manual_review" else "src/relationships/build.py", "rationale": "Curated taxonomic family assignment from reviewed DB++ metadata."}]})
    assignments.sort(key=lambda x: (x["relationship"], x["familyId"], x["sourceExerciseId"], x.get("targetExerciseId", "")))
    upstream_sha = db.get("metadata", {}).get("upstream", {}).get("sha256")
    return {"schemaVersion": SCHEMA_VERSION, "metadata": {"artifact": "exercise-relationships", "projectRelease": "1.5.0", "sourceDatabaseSchemaVersion": db.get("metadata", {}).get("schemaVersion"), "sourceExerciseCount": len(exercises), "generator": "src/relationships/build.py", "sourceSha256": generated_from or upstream_sha, "relationshipVocabulary": list(RELATIONSHIPS), "dimensionVocabulary": ["equipment", "grip", "stance", "angle", "laterality", "body_position", "load_position", "assistance", "resistance_type"], "semanticNotice": "Taxonomic/descriptive relationships do not imply physiological equivalence or substitution advice."}, "families": families, "relationships": assignments}

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("database"); parser.add_argument("output")
    args = parser.parse_args()
    db = json.loads(Path(args.database).read_text())
    doc = build_relationship_document(db)
    Path(args.output).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__": main()
