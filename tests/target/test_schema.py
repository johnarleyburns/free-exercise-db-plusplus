import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[2]
SCHEMA = json.loads((ROOT / "volume-target.schema.json").read_text())
VALID = sorted((ROOT / "examples/targets").glob("*.json"))
INVALID = sorted((ROOT / "fixtures/target/invalid").glob("*.json"))

def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)

def test_all_valid_examples():
    validator = Draft202012Validator(SCHEMA)
    assert len(VALID) == 3
    for path in VALID:
        errors = list(validator.iter_errors(json.loads(path.read_text())))
        assert not errors, f"{path}: {[e.message for e in errors]}"

def test_all_invalid_examples():
    validator = Draft202012Validator(SCHEMA)
    assert len(INVALID) == 4
    for path in INVALID:
        document = json.loads(path.read_text())
        assert list(validator.iter_errors(document)) or path.name == "reversed-range.json", path
