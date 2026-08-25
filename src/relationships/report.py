"""Deterministic coverage reports for relationship review."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from typing import Any
from .overrides import FAMILY_OVERRIDES
from .build import _family_for

def _coverage_breakdown(db, assigned, extractor):
    totals=Counter(); covered=Counter()
    for exercise_id,record in db["exercises"].items():
        values=extractor(record); values=values if isinstance(values,(list,tuple,set)) else [values]
        for value in values:
            label=value if value is not None else "unknown"; totals[label]+=1
            if exercise_id in assigned: covered[label]+=1
    return {key:{"total":totals[key],"assigned":covered[key],"unassigned":totals[key]-covered[key]} for key in sorted(totals)}

def reports(document: dict[str, Any], db: dict[str, Any]) -> dict[str, Any]:
    rows = document["relationships"]; members = [r for r in rows if r["relationship"] == "member_of_family"]
    assigned = {r["sourceExerciseId"] for r in members}; sizes = Counter(r["familyId"] for r in members)
    by_family={}
    for family_id in sorted(document["families"]):
        ids=[r["sourceExerciseId"] for r in members if r["familyId"]==family_id]
        by_family[family_id]={
            "movementPatterns":dict(sorted(Counter(p for eid in ids for p in db["exercises"][eid]["annotation"].get("patterns",())).items())),
            "equipment":dict(sorted(Counter(db["exercises"][eid]["source"].get("equipment") or "unknown" for eid in ids).items())),
            "categories":dict(sorted(Counter(db["exercises"][eid]["source"].get("category") or "unknown" for eid in ids).items())),
        }
    medium=sorted(r["sourceExerciseId"] for r in members if r["confidence"] == "medium")
    ambiguous=[]
    for exercise_id,record in sorted(db["exercises"].items()):
        candidates=_family_for(exercise_id,record,candidates_only=True)
        if len(candidates)>1: ambiguous.append({"exerciseId":exercise_id,"candidateFamilies":[family for family,_ in candidates],"reason":"multiple_high_confidence_rules"})
    category_coverage=_coverage_breakdown(db,assigned,lambda r:r["source"].get("category"))
    return {"totalExercises": len(db["exercises"]), "assignedExercises": len(assigned), "unassignedExercises": len(set(db["exercises"]) - assigned), "familyCount": len(document["families"]), "familySizes": dict(sorted(sizes.items())), "emptyFamilies": sorted(set(document["families"])-set(sizes)), "singleMemberFamilies": sorted(k for k,v in sizes.items() if v == 1), "largestFamilies": sorted(({"familyId":k,"size":v} for k,v in sizes.items()), key=lambda x:(-x["size"],x["familyId"])), "mediumConfidenceAssignments": medium, "manualOverrides":dict(sorted(FAMILY_OVERRIDES.items())), "coverageByGenre":category_coverage, "coverageByCategory":category_coverage, "coverageByMovementPattern":_coverage_breakdown(db,assigned,lambda r:r["annotation"].get("patterns",()) or ["unclassified"]), "coverageByEquipment":_coverage_breakdown(db,assigned,lambda r:r["source"].get("equipment")), "familyQuality":by_family, "reviewCandidates":[{"exerciseId":eid,"reason":"medium_confidence_taxonomy_judgment"} for eid in medium], "ambiguousCandidates":ambiguous, "unassigned": sorted(set(db["exercises"]) - assigned)}

def main() -> None:
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("database"); p.add_argument("relationships"); p.add_argument("output"); a=p.parse_args()
    db=json.loads(Path(a.database).read_text()); rel=json.loads(Path(a.relationships).read_text()); value=reports(rel,db)
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    (out.parent/"unassigned.json").write_text(json.dumps(value["unassigned"],indent=2)+"\n")
    (out.parent/"medium-confidence.json").write_text(json.dumps(value["mediumConfidenceAssignments"],indent=2)+"\n")
    (out.parent/"family-sizes.json").write_text(json.dumps(value["familySizes"],indent=2,sort_keys=True)+"\n")
    (out.parent/"review-candidates.json").write_text(json.dumps({"candidates":value["reviewCandidates"],"singleMemberFamilies":value["singleMemberFamilies"],"emptyFamilies":value["emptyFamilies"]},indent=2,sort_keys=True)+"\n")
    (out.parent/"ambiguous-candidates.json").write_text(json.dumps(value["ambiguousCandidates"],indent=2,sort_keys=True)+"\n")
if __name__ == "__main__": main()
