from src.analysis.policies import completed_set_count, planned_set_count
from src.analysis.units import UnitError, normalize_quantity


def test_units_are_explicit_and_conservative():
    assert normalize_quantity({"value": 1, "unit": "lb"}, "kg") == 0.45359237
    try:
        normalize_quantity({"value": 1, "unit": "%1RM"}, "kg")
    except UnitError:
        pass
    else:
        raise AssertionError("incompatible units must not be guessed")


def test_counting_policies_are_reusable():
    assert planned_set_count({"sets": {"min": 3, "target": 4, "max": 5}}) == 4
    assert planned_set_count({"plannedSets": [{}, {}]}) == 2
    workout = {"exercises": [{"sets": [
        {"completed": True, "setType": "working"},
        {"completed": False, "setType": "working"},
        {"completed": True, "setType": "warmup"},
    ]}]}
    assert completed_set_count(workout) == 2
    assert completed_set_count(workout, include_types={"working"}) == 1
