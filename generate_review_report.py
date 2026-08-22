#!/usr/bin/env python3
import argparse, csv, json
from collections import Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("db", type=Path)
    ap.add_argument("--markdown", type=Path, default=Path("REVIEW.md"))
    ap.add_argument("--csv", type=Path, default=Path("review-queue.csv"))
    ap.add_argument("--json", dest="json_out", type=Path, default=Path("review-summary.json"))
    args=ap.parse_args()

    db=json.loads(args.db.read_text(encoding="utf-8"))
    counts=Counter()
    reasons=Counter()
    rows=[]
    eligible=0
    for eid,r in db["exercises"].items():
        a=r["annotation"]; src=r["source"]
        counts[a["confidence"]]+=1
        if a["volumeEligible"]: eligible+=1
        for reason in a["reviewReasons"]: reasons[reason]+=1
        if a["confidence"]!="high" or a["reviewReasons"]:
            rows.append({
                "exerciseId":eid, "name":src.get("name",""), "category":src.get("category",""),
                "mechanic":src.get("mechanic"), "primary":", ".join(src.get("primaryMuscles",[])),
                "secondary":", ".join(src.get("secondaryMuscles",[])),
                "patterns":", ".join(a["patterns"]), "direct":", ".join(a["direct"]),
                "indirect":", ".join(a["indirect"]), "stabilizers":", ".join(a["stabilizers"]),
                "confidence":a["confidence"], "reviewReasons":"; ".join(a["reviewReasons"]),
            })
    rows.sort(key=lambda x: ({"low":0,"medium":1,"high":2}[x["confidence"]], x["name"].lower()))
    fields=["exerciseId","name","category","mechanic","primary","secondary","patterns","direct",
            "indirect","stabilizers","confidence","reviewReasons"]
    with args.csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    summary={"metadata":db["metadata"],"eligibleExercises":eligible,
             "confidenceCounts":dict(counts),"reviewReasonCounts":dict(reasons),
             "reviewQueueSize":len(rows),
             "lowConfidenceIds":[r["exerciseId"] for r in rows if r["confidence"]=="low"]}
    args.json_out.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")

    lines=["# Free Exercise DB++ Review Report","",
           f"- Source exercises: **{db['metadata']['sourceExerciseCount']}**",
           f"- Volume eligible: **{eligible}**",
           f"- High confidence: **{counts['high']}**",
           f"- Medium confidence: **{counts['medium']}**",
           f"- Low confidence: **{counts['low']}**",
           f"- Review queue: **{len(rows)}**","",
           "## Low-confidence exercises","",
           "| Exercise | Category | Primary | Secondary | Direct | Indirect | Reason |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["confidence"]!="low": continue
        vals=[r["name"],r["category"],r["primary"],r["secondary"],r["direct"],r["indirect"],r["reviewReasons"]]
        vals=[str(v).replace("|","\\|") for v in vals]
        lines.append("| "+" | ".join(vals)+" |")
    args.markdown.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(summary["confidenceCounts"], indent=2))
    print("review queue:", len(rows))

if __name__=="__main__":
    main()
