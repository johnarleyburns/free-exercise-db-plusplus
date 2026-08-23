#!/usr/bin/env python3
import json
import sys
from pathlib import Path

db = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
m = db["metadata"]

assert m["completeness"] == "full"
assert m["sourceExerciseCount"] == m["outputExerciseCount"]
assert m["outputExerciseCount"] == len(db["exercises"])
assert m["setCredits"] == {
    "direct": 1.0,
    "indirect": 0.5,
    "stabilizer": 0.0,
}

ontology = set(m["muscleOntology"])
evidence = m["evidence"]
refs = evidence["references"]
patterns = evidence["patterns"]

used_patterns = set()

for key, rec in db["exercises"].items():
    assert key == rec["exerciseId"], (key, rec["exerciseId"])

    ann = rec["annotation"]
    direct = set(ann["direct"])
    indirect = set(ann["indirect"])
    stabilizers = set(ann["stabilizers"])

    assert direct <= ontology
    assert indirect <= ontology
    assert stabilizers <= ontology

    assert not (direct & indirect), (key, "direct/indirect overlap")
    assert not (direct & stabilizers), (key, "direct/stabilizer overlap")
    assert not (indirect & stabilizers), (key, "indirect/stabilizer overlap")

    for pattern in ann["patterns"]:
        assert pattern in patterns, (key, pattern)
        used_patterns.add(pattern)

    for ref in ann["evidenceRefs"]:
        assert ref.startswith("pattern:"), (key, ref)
        pattern = ref.split(":", 1)[1]
        assert pattern in patterns, (key, ref)

for pattern in used_patterns:
    assert patterns[pattern]["status"] != "provisional", pattern

for pattern, pdata in patterns.items():
    for ref_id in pdata["references"]:
        assert ref_id in refs, (pattern, ref_id)

print(
    f"release contract passed: {len(db['exercises'])} exercises, "
    f"{len(used_patterns)} used patterns"
)
