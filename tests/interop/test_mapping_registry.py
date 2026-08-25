import json
from pathlib import Path
from src.interop.validate import validate_all
ROOT = Path(__file__).parents[2]
def test_all_mapping_registries():
    errors, warnings = validate_all(ROOT / "mappings", ROOT / "free-exercise-db-plusplus.json",
        ROOT / "interop-mapping.schema.json", ROOT / "exercise-interop-mapping.schema.json",
        ROOT / "mapping-loss.schema.json")
    assert not errors
    assert warnings == []
