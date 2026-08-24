#!/usr/bin/env python3
import json,sys
from pathlib import Path
db=json.loads(Path(sys.argv[1]).read_text())
allowed={"complex_pattern_bookkeeping","indirect_evidence_pattern","isolation_primary_secondary_fallback"}
bad=[]
for eid,r in db["exercises"].items():
    a=r["annotation"]
    if a["volumeEligible"] and a["confidence"]=="medium":
        reasons=set(a["reviewReasons"])
        if not reasons or not reasons <= allowed:
            bad.append((eid,sorted(reasons)))
assert not bad, f"unblessed medium-confidence mappings: {bad[:20]}"
print("all medium-confidence mappings have explicit blessed reasons")
