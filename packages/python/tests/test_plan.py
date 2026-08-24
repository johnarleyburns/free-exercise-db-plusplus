from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from fedbpp import Plan
ROOT=Path(__file__).parents[3]

def test_plan_consumer_loads_periodized_plan():
 plan=Plan.load(ROOT/"examples/plans/periodized-0.2.json")
 assert plan.document["schemaVersion"]=="0.2.0"
 assert len(plan.document["phases"])==2
