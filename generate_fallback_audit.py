#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("db", type=Path)
ap.add_argument("--out", type=Path, default=Path("FALLBACK-AUDIT.md"))
args=ap.parse_args()

db=json.loads(args.db.read_text(encoding="utf-8"))
rows=[]
for rec in db["exercises"].values():
    a=rec["annotation"]
    if not a["volumeEligible"]:
        continue
    if "isolation_primary_secondary_fallback" not in a.get("reviewReasons",[]):
        continue
    s=rec["source"]
    rows.append((s.get("name",""),s.get("mechanic"),", ".join(s.get("primaryMuscles",[])),", ".join(s.get("secondaryMuscles",[]))))

rows.sort(key=lambda x:x[0].lower())
lines=[
    "# DB++ Remaining Fallback Audit","",
    f"- Remaining isolation primary/secondary fallbacks: **{len(rows)}**","",
    "| Exercise | Mechanic | Primary | Secondary |",
    "|---|---|---|---|",
]
for row in rows:
    lines.append("| "+" | ".join(str(x).replace("|","\\|") for x in row)+" |")

args.out.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("remaining fallbacks:",len(rows))
