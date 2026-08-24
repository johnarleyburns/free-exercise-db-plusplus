#!/usr/bin/env python3
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("upstream",type=Path)
ap.add_argument("baseline_db",type=Path)
a=ap.parse_args()
up=json.loads(a.upstream.read_text())
base=json.loads(a.baseline_db.read_text())
new_ids={x["id"] for x in up}
old_ids=set(base["exercises"])
added=sorted(new_ids-old_ids); removed=sorted(old_ids-new_ids)
print(json.dumps({"baseline":len(old_ids),"upstream":len(new_ids),"added":added,"removed":removed},indent=2))
if removed:
    raise SystemExit("ERROR: upstream exercise IDs were removed/renamed; explicit compatibility review required")
if added:
    print("NOTICE: new upstream exercises detected; converter will classify them and audits must be reviewed before release")
