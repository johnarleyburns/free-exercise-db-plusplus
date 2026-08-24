#!/usr/bin/env python3
import json, sys
from pathlib import Path
db=json.loads(Path(sys.argv[1]).read_text())

# These are deliberately high-value semantic anchors. If one changes, review the mapping change.
EXPECTED = {
    "Barbell_Bench_Press_-_Medium_Grip": {
        "direct": {"chest"}, "indirect_contains": {"triceps","shoulders"}
    },
    "Pullups": {
        "direct_contains": {"lats"}, "indirect_contains": {"biceps"}
    },
}
for eid, exp in EXPECTED.items():
    assert eid in db["exercises"], f"missing golden exercise: {eid}"
    ann=db["exercises"][eid]["annotation"]
    if "direct" in exp:
        assert set(ann["direct"]) == exp["direct"], (eid,ann["direct"])
    if "direct_contains" in exp:
        assert exp["direct_contains"] <= set(ann["direct"]), (eid,ann["direct"])
    if "indirect_contains" in exp:
        assert exp["indirect_contains"] <= set(ann["indirect"]), (eid,ann["indirect"])
print("golden mapping anchors passed:",len(EXPECTED))
