#!/usr/bin/env python3
import argparse, csv, json
from collections import Counter
from pathlib import Path

ORDER = {"needs_review": 0, "rule_review": 1, "excluded_verified": 2, "reviewed": 3}

def priority(a):
    if a["confidence"] == "low":
        return "needs_review"
    if not a["volumeEligible"]:
        return "excluded_verified"
    if a["confidence"] == "medium" or a["reviewReasons"]:
        return "rule_review"
    return "reviewed"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("db", type=Path)
    ap.add_argument("--markdown", type=Path, default=Path("REVIEW.md"))
    ap.add_argument("--csv", type=Path, default=Path("review-queue.csv"))
    ap.add_argument("--json", dest="json_out", type=Path, default=Path("review-summary.json"))
    args=ap.parse_args()

    db=json.loads(args.db.read_text(encoding="utf-8"))
    conf, reasons, prios = Counter(), Counter(), Counter()
    rows=[]; eligible=0
    for eid,r in db["exercises"].items():
        a=r["annotation"]; src=r["source"]; p=priority(a)
        conf[a["confidence"]]+=1; prios[p]+=1
        if a["volumeEligible"]: eligible+=1
        for reason in a["reviewReasons"]: reasons[reason]+=1
        rows.append({
            "reviewPriority":p,"exerciseId":eid,"name":src.get("name",""),
            "category":src.get("category",""),"mechanic":src.get("mechanic"),
            "primary":", ".join(src.get("primaryMuscles",[])),
            "secondary":", ".join(src.get("secondaryMuscles",[])),
            "patterns":", ".join(a["patterns"]),"direct":", ".join(a["direct"]),
            "indirect":", ".join(a["indirect"]),"stabilizers":", ".join(a["stabilizers"]),
            "confidence":a["confidence"],"reviewReasons":"; ".join(a["reviewReasons"]),
        })

    rows.sort(key=lambda r:(ORDER[r["reviewPriority"]],r["name"].lower()))
    queue=[r for r in rows if r["reviewPriority"] in {"needs_review","rule_review"}]
    fields=list(queue[0].keys()) if queue else list(rows[0].keys())
    with args.csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(queue)

    summary={
        "metadata":db["metadata"],"eligibleExercises":eligible,
        "confidenceCounts":dict(conf),"reviewPriorityCounts":dict(prios),
        "reviewReasonCounts":dict(reasons),"reviewQueueSize":len(queue),
        "lowConfidenceIds":[r["exerciseId"] for r in rows if r["reviewPriority"]=="needs_review"]
    }
    args.json_out.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")

    lines=["# Free Exercise DB++ Review Report","",
           f"- Source exercises: **{db['metadata']['sourceExerciseCount']}**",
           f"- Volume eligible: **{eligible}**",
           f"- Needs review: **{prios['needs_review']}**",
           f"- Rule review: **{prios['rule_review']}**",
           f"- Excluded / verified: **{prios['excluded_verified']}**",
           f"- Reviewed / high: **{prios['reviewed']}**","",
           "## Needs review","",
           "| Exercise | Category | Primary | Secondary | Direct | Indirect | Reason |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["reviewPriority"]!="needs_review": continue
        vals=[r["name"],r["category"],r["primary"],r["secondary"],r["direct"],r["indirect"],r["reviewReasons"]]
        lines.append("| "+" | ".join(str(v).replace("|","\\|") for v in vals)+" |")
    args.markdown.write_text("\n".join(lines)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
