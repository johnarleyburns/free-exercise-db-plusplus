import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from fedbpp import Database, RelationshipRegistry, Workout, ValidationError
ROOT=Path(__file__).parents[3]
def test_database_lookup_and_search():
    db=Database.load(ROOT/"free-exercise-db-plusplus.json")
    assert len(db) > 800
    assert db.get_exercise("Barbell_Bench_Press_-_Medium_Grip").volume_eligible
    assert db.find_exercises("bench")
    assert db.exercises_for_muscle("chest")
    try: db.get_exercise("missing")
    except KeyError: pass
    else: raise AssertionError("missing exercise must fail")
def test_workout_validation_and_effective_sets():
    db=Database.load(ROOT/"free-exercise-db-plusplus.json")
    workout=Workout.load(ROOT/"examples/workouts/basic-barbell.json")
    totals=workout.effective_sets(db)
    assert totals and all(value > 0 for value in totals.values())
def test_invalid_workout_rejected():
    try: Workout.load(ROOT/"fixtures/workout/wrong-version.json")
    except ValidationError: pass
    else: raise AssertionError("invalid fixture must fail")
def test_packaged_relationship_artifact():
    registry=RelationshipRegistry.load()
    assert registry.family_for("Dumbbell_Bench_Press").family_id=="bench_press"
    assert "Barbell_Bench_Press_-_Medium_Grip" in registry.members("bench_press")
