import json
from pathlib import Path
from jsonschema import Draft202012Validator
def validate_all(mapping_dir,db_path,schema_path,crosswalk_schema_path):
 root=Path(mapping_dir); ids=set(json.loads(Path(db_path).read_text())["exercises"]); errors=[]; warnings=[]
 for f in sorted(root.glob("*.json")):
  d=json.loads(f.read_text()); schema=json.loads(Path(crosswalk_schema_path if any("externalId" in e for e in d.get("entries",[])) else schema_path).read_text()); errors += [f"{f}: {e.message}" for e in Draft202012Validator(schema).iter_errors(d)]
  for e in d.get("entries",[]):
   for x in e.get("dbppExerciseIds",[]):
    if x not in ids: errors.append(f"{f}: unknown DB++ exerciseId {x}")
   if e.get("relation")=="unmapped": warnings.append(f"{f}: unmapped {e.get('externalId','')}")
 return errors,warnings
