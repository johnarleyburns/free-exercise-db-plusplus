import json,sys
from pathlib import Path
db=json.loads(Path(sys.argv[1]).read_text())
m=db["metadata"]
assert m["completeness"]=="full"
assert m["sourceExerciseCount"]==m["outputExerciseCount"]==len(db["exercises"])
assert m["setCredits"]=={"direct":1.0,"indirect":0.5,"stabilizer":0.0}
ontology=set(m["muscleOntology"]); ev=m["evidence"]; used=set()
for key,r in db["exercises"].items():
    assert key==r["exerciseId"]
    a=r["annotation"]
    groups=[set(a["direct"]),set(a["indirect"]),set(a["stabilizers"])]
    assert all(g<=ontology for g in groups)
    assert not(groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
    for p in a["patterns"]:
        assert p in ev["patterns"]; used.add(p)
    for ref in a["evidenceRefs"]:
        assert ref.startswith("pattern:") and ref.split(":",1)[1] in ev["patterns"]
for p in used: assert ev["patterns"][p]["status"]!="provisional"
for p,d in ev["patterns"].items():
    for rid in d["references"]: assert rid in ev["references"],(p,rid)
print("release contract passed:",len(db["exercises"]),"exercises,",len(used),"used patterns")
