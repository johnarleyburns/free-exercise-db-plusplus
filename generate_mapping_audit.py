#!/usr/bin/env python3
import argparse, csv, json
from collections import Counter
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("db", type=Path)
ap.add_argument("--markdown", type=Path, default=Path("MAPPING-AUDIT.md"))
ap.add_argument("--csv", type=Path, default=Path("mapping-audit.csv"))
args=ap.parse_args()

db=json.loads(args.db.read_text(encoding="utf-8"))
evidence=db["metadata"]["evidence"]["patterns"]

rows=[]
reason_counts=Counter()
for eid,rec in db["exercises"].items():
    a=rec["annotation"]; src=rec["source"]
    if not a["volumeEligible"]:
        continue
    if a["confidence"]=="high" and not a.get("reviewReasons"):
        continue

    pattern_statuses=[evidence[p]["status"] for p in a.get("patterns",[])]
    evidence_status=",".join(pattern_statuses) if pattern_statuses else "fallback"
    for reason in a.get("reviewReasons",[]):
        reason_counts[reason]+=1

    source_primary=src.get("primaryMuscles",[])
    source_secondary=src.get("secondaryMuscles",[])
    mapped=set(a.get("direct",[]))|set(a.get("indirect",[]))|set(a.get("stabilizers",[]))
    source=set(source_primary)|set(source_secondary)

    rows.append({
        "exerciseId":eid,
        "name":src.get("name",""),
        "category":src.get("category",""),
        "mechanic":src.get("mechanic"),
        "patterns":", ".join(a.get("patterns",[])),
        "evidenceStatus":evidence_status,
        "sourcePrimary":", ".join(source_primary),
        "sourceSecondary":", ".join(source_secondary),
        "direct":", ".join(a.get("direct",[])),
        "indirect":", ".join(a.get("indirect",[])),
        "stabilizers":", ".join(a.get("stabilizers",[])),
        "confidence":a["confidence"],
        "reviewReasons":"; ".join(a.get("reviewReasons",[])),
        "sourceOnlyMuscles":", ".join(sorted(source-mapped)),
        "dbppOnlyMuscles":", ".join(sorted(mapped-source)),
    })

rows.sort(key=lambda r:(
    0 if r["evidenceStatus"]=="fallback" else
    1 if "indirect_support" in r["evidenceStatus"] else
    2,
    r["name"].lower()
))

fields=list(rows[0].keys()) if rows else []
with args.csv.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader(); w.writerows(rows)

fallbacks=[r for r in rows if r["evidenceStatus"]=="fallback"]
indirect=[r for r in rows if "indirect_support" in r["evidenceStatus"]]
complex_rows=[r for r in rows if "complex_supported" in r["evidenceStatus"]]

lines=[
    "# DB++ Exercise-Specific Mapping Audit","",
    f"- Audited non-high volume mappings: **{len(rows)}**",
    f"- Upstream primary/secondary fallbacks: **{len(fallbacks)}**",
    f"- Indirect-evidence pattern mappings: **{len(indirect)}**",
    f"- Complex-supported pattern mappings: **{len(complex_rows)}**","",
    "## Remaining fallbacks","",
    "| Exercise | Mechanic | Source primary | Source secondary | DB++ direct | DB++ indirect |",
    "|---|---|---|---|---|---|"
]
for r in fallbacks:
    vals=[r["name"],r["mechanic"],r["sourcePrimary"],r["sourceSecondary"],r["direct"],r["indirect"]]
    lines.append("| "+" | ".join(str(v).replace("|","\\|") for v in vals)+" |")

lines += ["","## Indirect-support mappings","",
          "| Exercise | Pattern | Direct | Indirect | Source-only | DB++-only |",
          "|---|---|---|---|---|---|"]
for r in indirect:
    vals=[r["name"],r["patterns"],r["direct"],r["indirect"],r["sourceOnlyMuscles"],r["dbppOnlyMuscles"]]
    lines.append("| "+" | ".join(str(v).replace("|","\\|") for v in vals)+" |")

args.markdown.write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps({
    "audited":len(rows),
    "fallbacks":len(fallbacks),
    "indirectSupport":len(indirect),
    "complexSupported":len(complex_rows),
    "reasonCounts":dict(reason_counts)
},indent=2))
