from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).parents[2]; sys.path.insert(0,str(ROOT))
from src.analysis.export import plan_coverage_rows, plan_actual_rows,  write_plan_coverage_csv, write_plan_actual_csv

def test_research_exports_are_tidy_and_deterministic():
 with tempfile.TemporaryDirectory() as directory:
  tmp_path=Path(directory)
  analysis={"nativeCycle":{"effectiveSets":{"chest":4.0},"directSets":{},"indirectSets":{},"stabilizerParticipationSets":{},"movementPatternSets":{}},"normalized7Day":{"effectiveSets":{},"directSets":{},"indirectSets":{},"stabilizerParticipationSets":{},"movementPatternSets":{}}}
  result={"adherence":{"muscles":{"chest":{"planned":4,"actual":3,"delta":-1,"fraction":.75}},"movementPatterns":{}}}
  assert plan_coverage_rows(analysis)[0]["key"]=="chest"; assert plan_actual_rows(result)[0]["fraction"]==.75
  a=tmp_path/"coverage.csv"; b=tmp_path/"actual.csv";  write_plan_coverage_csv(analysis,a); write_plan_actual_csv(result,b); assert a.read_text().endswith("\n") and b.read_text().endswith("\n")
