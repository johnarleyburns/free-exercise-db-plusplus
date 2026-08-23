#!/usr/bin/env python3
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("db", type=Path)
ap.add_argument("--out", type=Path, default=Path("RULE-AUDIT.md"))
args=ap.parse_args()

db=json.loads(args.db.read_text(encoding="utf-8"))
evidence=db["metadata"]["evidence"]["patterns"]

by_pattern=defaultdict(Counter)
examples=defaultdict(list)

for rec in db["exercises"].values():
    ann=rec["annotation"]
    for pattern in ann.get("patterns", []):
        by_pattern[pattern][ann["confidence"]] += 1
        if len(examples[pattern]) < 4:
            examples[pattern].append(rec["source"].get("name", rec["exerciseId"]))

rows=[]
for pattern, counts in by_pattern.items():
    rows.append((
        sum(counts.values()),
        pattern,
        evidence[pattern]["status"],
        counts["high"],
        counts["medium"],
        counts["low"],
        examples[pattern],
    ))

rows.sort(key=lambda r: (r[2] != "supported", -r[0], r[1]))

medium_by_status=Counter()
for n,p,status,high,medium,low,ex in rows:
    medium_by_status[status]+=medium

lines=[
    "# DB++ Rule Quality Audit","",
    f"- Recognized pattern uses: **{sum(r[0] for r in rows)}**",
    f"- High-confidence recognized uses: **{sum(r[3] for r in rows)}**",
    f"- Medium complex-supported uses: **{medium_by_status['complex_supported']}**",
    f"- Medium indirect-support uses: **{medium_by_status['indirect_support']}**",
    f"- Medium provisional uses: **{medium_by_status['provisional']}**","",
    "## Pattern confidence distribution","",
    "| Pattern | Evidence | Uses | High | Medium | Examples |",
    "|---|---|---:|---:|---:|---|"
]
for n,p,status,high,medium,low,ex in rows:
    lines.append(f"| `{p}` | {status} | {n} | {high} | {medium} | {', '.join(ex)} |")

args.out.write_text("\n".join(lines)+"\n", encoding="utf-8")
