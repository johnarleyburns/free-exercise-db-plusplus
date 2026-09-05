#!/usr/bin/env python3
"""Contract checks for DB++-owned catalog additions."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "src/catalog_additions.json").read_text(encoding="utf-8"))
db = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
relationships = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

entries = manifest["entries"]
assert len(entries) == 54
assert len({entry["id"] for entry in entries}) == len(entries)
assert manifest["reviewedOn"] == "2026-09-05"
assert {"keiser", "hammer_strength", "precor", "life_fitness", "matrix"} <= set(manifest["vendorSources"])

for entry in entries:
    assert entry["id"] in db["exercises"], entry["id"]
    assert entry["vendors"]
    assert set(entry["patterns"]) <= set(db["metadata"]["evidence"]["patterns"])
    record = db["exercises"][entry["id"]]
    assert record["source"]["images"] == []
    assert record["source"].get("aliases", []) == entry.get("aliases", [])
    assert record["annotation"]["patterns"] == entry["patterns"]
    assert record["annotation"]["direct"] == entry["direct"]

assert db["metadata"]["curatedExerciseCount"] == 54
assert db["metadata"]["upstreamExerciseCount"] == 873
assert db["metadata"]["outputExerciseCount"] == 927
assert db["exercises"]["Cable_Push_Pull"]["source"]["name"] == "Cable Push-Pull"
assert db["exercises"]["Machine_Rotary_Torso"]["source"]["name"] == "Machine Rotary Torso"

mapped = {row["sourceExerciseId"]: row for row in relationships["relationships"]}
for entry in entries:
    assert mapped[entry["id"]]["familyId"] == entry["family"]
    assert mapped[entry["id"]]["confidence"] == "high"

print("catalog expansion contract passed: 54 curated exercises, 927 total")
