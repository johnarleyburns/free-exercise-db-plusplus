#!/usr/bin/env python3
import argparse, json
from collections import Counter
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("db", type=Path)
ap.add_argument("--out", type=Path, default=Path("EVIDENCE-AUDIT.md"))
a=ap.parse_args()
db=json.loads(a.db.read_text())
ev=db["metadata"]["evidence"]["patterns"]
usage=Counter()
for rec in db["exercises"].values():
    for p in rec["annotation"].get("patterns",[]): usage[p]+=1
rows=sorted(((usage[p],p,e["status"],e["references"]) for p,e in ev.items()),
            key=lambda x:(x[2]!="provisional",-x[0],x[1]))
prov=[r for r in rows if r[2]=="provisional"]
lines=["# DB++ Evidence Audit","",
       f"- Canonical patterns: **{len(ev)}**",
       f"- Provisional patterns: **{len(prov)}**",
       f"- Exercise-pattern uses still provisional: **{sum(r[0] for r in prov)}**","",
       "## Remaining provisional patterns","",
       "| Pattern | Exercise uses |","|---|---:|"]
lines += [f"| `{p}` | {n} |" for n,p,_,_ in prov]
a.out.write_text("\n".join(lines)+"\n")
