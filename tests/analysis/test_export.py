from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).parents[2]; sys.path.insert(0,str(ROOT))
from src.analysis.export import exercise_research_rows, muscle_research_rows, plan_coverage_rows, plan_actual_rows, write_exercise_research_csv, write_muscle_research_csv, write_plan_coverage_csv, write_plan_actual_csv

def test_research_exports_are_tidy_and_deterministic():
 with tempfile.TemporaryDirectory() as directory:
  tmp_path=Path(directory)
  analysis={"nativeCycle":{"effectiveSets":{"chest":4.0},"directSets":{},"indirectSets":{},"stabilizerParticipationSets":{},"movementPatternSets":{}},"normalized7Day":{"effectiveSets":{},"directSets":{},"indirectSets":{},"stabilizerParticipationSets":{},"movementPatternSets":{}}}
  result={"adherence":{"muscles":{"chest":{"planned":4,"actual":3,"delta":-1,"fraction":.75}},"movementPatterns":{}}}
  assert plan_coverage_rows(analysis)[0]["key"]=="chest"; assert plan_actual_rows(result)[0]["fraction"]==.75
  a=tmp_path/"coverage.csv"; b=tmp_path/"actual.csv";  write_plan_coverage_csv(analysis,a); write_plan_actual_csv(result,b); assert a.read_text().endswith("\n") and b.read_text().endswith("\n")


def test_muscle_and_exercise_research_exports_preserve_identifiers_and_ranges():
 result={"analysisPolicy":"dbpp-default-volume-v1","analysisMetadata":{"analysisPolicy":"dbpp-default-volume-v1","dbSchemaVersion":"0.3.0","dbConverterVersion":"0.8.0","planSchemaVersion":"0.2.0","workoutSchemaVersion":"0.3.0"},"plan":{"planId":"p","revisionId":"r"},"actual":{"sessionId":"a"},"matching":{"planSessionId":"s","exercises":[{"prescriptionId":"rx","plannedExerciseId":"bench","actualExerciseId":"bench","status":"matched","plannedSetRange":{"min":3,"target":4,"max":5},"actualCompletedSets":4}]},"adherence":{"muscles":{"chest":{"direct":{"planned":4,"actual":4},"indirect":{"planned":0,"actual":0},"stabilizerParticipation":{"planned":0,"actual":0},"effective":{"planned":4,"actual":4,"fraction":1}}}}}
 muscles=muscle_research_rows(result,"athlete"); exercises=exercise_research_rows(result,"athlete")
 assert muscles[0]["subject_id"]=="athlete" and muscles[0]["planned_direct_sets"]==4
 assert exercises[0]["planned_sets_min"]==3 and exercises[0]["planned_sets_max"]==5
 with tempfile.TemporaryDirectory() as directory:
  a=Path(directory)/"muscle.csv"; b=Path(directory)/"exercise.csv"
  write_muscle_research_csv(result,a,"athlete"); write_exercise_research_csv(result,b,"athlete")
  assert a.read_text().endswith("\n") and b.read_text().endswith("\n")
