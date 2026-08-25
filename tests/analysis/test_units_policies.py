from src.analysis.policies import add_ranges, completed_set_count, normalize_range, planned_set_count, representative_scalar, scale_range, set_credits
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
    assert planned_set_count({"plannedSets": [{"setType": "working"}, {"setType": "working"}]}) == 2
    workout = {"exercises": [{"sets": [
        {"completed": True, "setType": "working"},
        {"completed": False, "setType": "working"},
        {"completed": True, "setType": "warmup"},
    ]}]}
    assert completed_set_count(workout) == 1
    assert completed_set_count(workout, include_types={"working"}) == 1

def test_partial_ranges_remain_partial_and_scalar_selection_is_explicit():
    assert normalize_range({"min":3}) == {"min":3.0,"target":None,"max":None}
    assert normalize_range({"target":4}) == {"min":None,"target":4.0,"max":None}
    assert normalize_range({"max":5}) == {"min":None,"target":None,"max":5.0}
    assert normalize_range({"min":3,"max":5}) == {"min":3.0,"target":None,"max":5.0}
    assert normalize_range({"min":3,"target":4,"max":5}) == {"min":3.0,"target":4.0,"max":5.0}
    assert [representative_scalar(v) for v in ({"min":3},{"target":4},{"max":5},{"min":3,"target":4,"max":5})] == [3,4,5,4]
    assert scale_range({"min":3},2) == {"min":6.0,"target":None,"max":None}
    assert add_ranges({"min":3},{"min":2}) == {"min":5.0,"target":None,"max":None}
    assert add_ranges({"min":3},{"max":5}) == {"min":None,"target":None,"max":None}

def test_set_credits_are_strict_with_explicit_legacy_fallback():
    valid={"metadata":{"setCredits":{"direct":1,"indirect":.5,"stabilizer":0}}}
    assert set_credits(valid) == {"direct":1.0,"indirect":.5,"stabilizer":0.0}
    for invalid in (
        {"metadata":{}},
        {"metadata":{"setCredits":{"direct":1,"indirect":.5}}},
        {"metadata":{"setCredits":{"direct":"1","indirect":.5,"stabilizer":0}}},
        {"metadata":{"setCredits":{"direct":float("nan"),"indirect":.5,"stabilizer":0}}},
    ):
        try: set_credits(invalid)
        except ValueError: pass
        else: raise AssertionError("malformed set credits must fail")
    assert set_credits({"metadata":{}},allow_legacy_defaults=True) == {"direct":1.0,"indirect":.5,"stabilizer":0.0}
