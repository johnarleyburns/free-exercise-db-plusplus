import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "packages/python"))
sys.path.insert(0, str(ROOT))

from fedbpp import Database, FamilyMappingRegistry, MappingRegistry, RelationshipRegistry
from fedbpp.analysis import analyze_plan, compare_plan_actual, compare_plans
from fedbpp.relationships import family_coverage
from jsonschema import Draft202012Validator, FormatChecker
from src.relationships.build import build_relationship_document
from src.relationships.validate import validate_relationship_document
from src.interop.validate import validate_family_mapping

def load(name): return json.loads((ROOT/name).read_text())

DB_DOCUMENT=load("free-exercise-db-plusplus.json")
RELATIONSHIPS=load("exercise-relationships.json")
SCHEMA=load("exercise-relationships.schema.json")

def schema_errors(document): return list(Draft202012Validator(SCHEMA,format_checker=FormatChecker()).iter_errors(document))

def test_artifact_schema_semantics_and_reproducibility():
    assert not schema_errors(RELATIONSHIPS)
    assert validate_relationship_document(RELATIONSHIPS,DB_DOCUMENT)==[]
    assert build_relationship_document(DB_DOCUMENT)==RELATIONSHIPS
    assert RELATIONSHIPS["schemaVersion"]=="0.1.0"
    regenerated=copy.deepcopy(DB_DOCUMENT); regenerated["metadata"]["generatedAt"]="2099-01-01T00:00:00Z"
    assert build_relationship_document(regenerated)==RELATIONSHIPS

def test_schema_rejects_invalid_values_and_extra_properties():
    cases=[]
    bad=copy.deepcopy(RELATIONSHIPS); bad["families"]["Bad Family!"]=bad["families"].pop("bench_press"); cases.append(bad)
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"][0]["relationship"]="equivalent_to"; cases.append(bad)
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"][0]["confidence"]="low"; cases.append(bad)
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"][0]["unexpected"]=True; cases.append(bad)
    assert all(schema_errors(case) for case in cases)

def test_semantic_validator_rejects_ids_duplicates_and_contradictions():
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"][0]["sourceExerciseId"]="missing"; assert any("unknown source" in e for e in validate_relationship_document(bad,DB_DOCUMENT))
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"].append(copy.deepcopy(bad["relationships"][0])); assert any("duplicate" in e for e in validate_relationship_document(bad,DB_DOCUMENT))
    bad=copy.deepcopy(RELATIONSHIPS); bad["relationships"][0]["dimensions"]["equipment"]="dumbbell"; assert any("equipment contradiction" in e for e in validate_relationship_document(bad,DB_DOCUMENT))

def test_full_golden_family_memberships():
    golden=load("tests/relationships/golden-families.json")["families"]
    registry=RelationshipRegistry.from_dict(RELATIONSHIPS)
    assert {family:registry.members(family) for family in golden}==golden

def test_deterministic_coverage_and_quality_reports():
    summary=load("reports/relationships/summary.json")
    assert summary["totalExercises"]==873 and summary["assignedExercises"]==286 and summary["unassignedExercises"]==587
    assert summary["familyCount"]==16 and summary["emptyFamilies"]==[] and summary["ambiguousCandidates"]==[]
    assert all(key in summary for key in ("coverageByGenre","coverageByMovementPattern","coverageByEquipment","familyQuality","manualOverrides"))
    for name in ("unassigned.json","medium-confidence.json","family-sizes.json","review-candidates.json","ambiguous-candidates.json"):
        assert (ROOT/"reports/relationships"/name).is_file()

def test_edge_case_boundaries_are_explicit():
    registry=RelationshipRegistry.from_dict(RELATIONSHIPS)
    assert registry.family_for("Chin-Up").family_id=="chin_up"
    assert registry.family_for("Pullups").family_id=="pull_up"
    assert registry.family_for("Romanian_Deadlift").family_id=="romanian_deadlift"
    assert registry.family_for("Barbell_Deadlift").family_id=="deadlift"
    assert registry.family_for("Barbell_Hip_Thrust").family_id=="hip_thrust"
    assert registry.family_for("Barbell_Glute_Bridge").family_id=="glute_bridge"
    for exercise_id in ("Upright_Barbell_Row","Pushups","Cable_Chest_Press","Good_Morning","Squat_Jerk","Triceps_Stretch","Seated_Band_Hamstring_Curl"):
        assert registry.family_for(exercise_id) is None

def test_family_aliases_dimensions_and_dynamic_relationships():
    registry=RelationshipRegistry.from_dict(RELATIONSHIPS)
    assert registry.search_families("RDL")[0].family_id=="romanian_deadlift"
    pairs={
        "equipment":("Barbell_Bench_Press_-_Medium_Grip","Dumbbell_Bench_Press"),
        "grip":("Barbell_Bench_Press_-_Medium_Grip","Close-Grip_Barbell_Bench_Press"),
        "stance":("Barbell_Squat","Wide_Stance_Barbell_Squat"),
        "angle":("Barbell_Bench_Press_-_Medium_Grip","Barbell_Incline_Bench_Press_-_Medium_Grip"),
        "laterality":("Dumbbell_Bench_Press","One_Arm_Dumbbell_Bench_Press"),
    }
    for dimension,(left,right) in pairs.items():
        comparison=registry.compare_dimensions(left,right); assert comparison["sameFamily"] and dimension in comparison["differences"]
    assert registry.relationship(*pairs["equipment"]).relationship=="equipment_variant_of"
    assert registry.relationship("Barbell_Bench_Press_-_Medium_Grip","Barbell_Squat") is None

def test_related_candidates_and_structural_coverage_are_descriptive():
    db=Database.load(ROOT/"free-exercise-db-plusplus.json"); registry=RelationshipRegistry.from_dict(RELATIONSHIPS,db=db)
    candidates=registry.related_candidates("Barbell_Bench_Press_-_Medium_Grip",equipment="dumbbell")
    assert any(row.target_exercise_id=="Dumbbell_Bench_Press" for row in candidates)
    result=registry.compare_exercise_coverage("Barbell_Bench_Press_-_Medium_Grip","Dumbbell_Bench_Press")
    assert result["structural"]["sameFamily"] is True
    assert "effectiveSetDelta" in result["coverageDifference"]
    assert "equivalent" not in json.dumps(result).casefold() and "substitute" not in json.dumps(result).casefold()

def test_plan_family_coverage_ranges_and_comparison():
    registry=RelationshipRegistry.from_dict(RELATIONSHIPS)
    plan_a={"schemaVersion":"0.1.0","planId":"p","revisionId":"a","cycle":{"lengthDays":7},"sessions":[{"planSessionId":"s","dayOffset":0,"exercises":[{"prescriptionId":"x","exerciseId":"Barbell_Bench_Press_-_Medium_Grip","order":1,"sets":{"min":3,"target":4,"max":5},"reps":8}]}]}
    plan_b=copy.deepcopy(plan_a); plan_b["revisionId"]="b"; plan_b["sessions"][0]["exercises"][0]["exerciseId"]="Dumbbell_Bench_Press"
    coverage=family_coverage(plan_a,registry)["bench_press"]
    assert coverage["plannedSetRanges"]=={"min":3.0,"target":4.0,"max":5.0} and coverage["sessionExposures"]==1
    assert analyze_plan(plan_a,DB_DOCUMENT,registry)["familyCoverage"]["bench_press"]["plannedSets"]==4.0
    result=compare_plans(plan_a,plan_b,DB_DOCUMENT,registry)
    assert result["familyComparison"]["inBoth"]==["bench_press"]
    assert result["familyComparison"]["variantDifferences"]["bench_press"]["sameFamily"] is True
    assert "equipment" in result["familyComparison"]["variantDifferences"]["bench_press"]["dimensionDifferences"][0]["differences"]

def test_explicit_actual_substitution_is_enriched_not_decided():
    registry=RelationshipRegistry.from_dict(RELATIONSHIPS)
    plan={"schemaVersion":"0.1.0","planId":"p","revisionId":"a","cycle":{"lengthDays":7},"sessions":[{"planSessionId":"s","dayOffset":0,"exercises":[{"prescriptionId":"x","exerciseId":"Barbell_Bench_Press_-_Medium_Grip","order":1,"sets":1,"reps":8}]}]}
    actual={"schemaVersion":"0.3.0","sessionId":"a","startTime":"2026-01-01T00:00:00Z","planReference":{"planId":"p","revisionId":"a","planSessionId":"s"},"exercises":[{"exerciseId":"Dumbbell_Bench_Press","exercisePrescriptionId":"x","substitution":{"plannedPrescriptionId":"x","reason":"equipment"},"order":1,"sets":[{"setNumber":1,"setType":"working","reps":8,"completed":True}]}]}
    result=compare_plan_actual(plan,actual,DB_DOCUMENT,registry); row=result["matching"]["exercises"][0]
    assert row["status"]=="substitution" and row["relationshipContext"]["sameFamily"] is True
    assert "acceptable" not in json.dumps(row).casefold()

def test_family_interop_is_separate_from_exact_identity():
    family_schema=load("family-interop-mapping.schema.json"); fixture=load("fixtures/interop/family-mapping-example.json")
    assert not list(Draft202012Validator(family_schema,format_checker=FormatChecker()).iter_errors(fixture))
    assert not validate_family_mapping(fixture,ROOT/"family-interop-mapping.schema.json",RELATIONSHIPS)
    match=FamilyMappingRegistry.load(ROOT/"fixtures/interop/family-mapping-example.json").lookup_external("example-broad-vocabulary","BENCH_PRESS")[0]
    assert match.family_id=="bench_press" and match.relation=="broader"
    exact=MappingRegistry.load(ROOT/"mappings/garmin-fit-exercises.json").lookup_external("garmin-fit","exercise_name.bench_press.DUMBBELL_BENCH_PRESS")
    assert len(exact)==1 and exact[0].relation=="exact" and exact[0].dbpp_exercise_id=="Dumbbell_Bench_Press"
    audit=load("reports/interop/garmin-fit-families.json"); garmin=load("mappings/garmin-fit-exercises.json")
    assert audit["exactExerciseMappings"]==len(garmin["entries"])==16
    assert audit["familyLevelMappings"]==0 and {entry["relation"] for entry in garmin["entries"]}=={"exact"}
