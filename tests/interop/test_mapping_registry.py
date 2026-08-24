import json
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT = Path(__file__).parents[2]
def test_all_mapping_registries():
    schema=json.loads((ROOT / "interop-mapping.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator=Draft202012Validator(schema)
    files=sorted((ROOT / "mappings").glob("*.json"))
    assert files
    for path in files:
        mapping=json.loads(path.read_text())
        errors=list(validator.iter_errors(mapping))
        assert not errors, f"{path}: {[e.message for e in errors]}"
        pairs=[(e["sourcePath"],e["targetField"]) for e in mapping["entries"]]
        assert len(pairs)==len(set(pairs)), path
        if mapping["status"] != "placeholder":
            assert mapping["entries"], path
