import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA = json.loads((ROOT / "workout.schema.json").read_text())
VALID = sorted((ROOT / "examples/workouts").glob("*.json"))
INVALID = sorted((ROOT / "fixtures/workout").glob("*.json"))

def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)

def test_all_valid_examples():
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    assert len(VALID) >= 10
    for path in VALID:
        errors = list(validator.iter_errors(json.loads(path.read_text())))
        assert not errors, f"{path}: {errors}"

def test_all_invalid_examples():
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    assert len(INVALID) >= 3
    for path in INVALID:
        assert list(validator.iter_errors(json.loads(path.read_text()))), path
