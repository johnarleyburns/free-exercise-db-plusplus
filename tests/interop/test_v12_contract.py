import json
import sys
sys.path.insert(0, str(Path(__file__).parents[2])) if "Path" in globals() else None
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
ROOT=Path(__file__).parents[2]
def test_crosswalk_and_ambiguity():
 s=json.loads((ROOT/"exercise-interop-mapping.schema.json").read_text()); d=json.loads((ROOT/"mappings/health-connect-exercises.json").read_text())
 assert not list(Draft202012Validator(s,format_checker=FormatChecker()).iter_errors(d))
 from src.interop.registry import MappingRegistry
 r=MappingRegistry.load(ROOT/"mappings/health-connect-exercises.json")
 assert len(r.lookup_external("android-health-connect","EXERCISE_SESSION_TYPE_STRENGTH_TRAINING")) > 1
def test_loss_schema():
 s=json.loads((ROOT/"mapping-loss.schema.json").read_text()); fixture=json.loads((ROOT/"fixtures/interop/health-connect/unmapped-rir.json").read_text())
 assert fixture["loss"]["status"] in s["properties"]["status"]["enum"]
if __name__=="__main__":
 test_crosswalk_and_ambiguity(); test_loss_schema(); print("v1.2 contract tests passed")
