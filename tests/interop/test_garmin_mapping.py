import json
from pathlib import Path

ROOT = Path(__file__).parents[2]

def test_garmin_mapping_registry():
    mapping = json.loads((ROOT / "mappings/garmin-fit.json").read_text())
    assert mapping["target"] == "garmin-fit"
    assert mapping["mappingVersion"] == "0.1.0"
    entries = mapping["entries"]
    assert len(entries) >= 10
    allowed = {"exact", "compatible", "lossy", "extension_required", "unsupported"}
    assert all(entry["quality"] in allowed for entry in entries)
    paths = [entry["sourcePath"] for entry in entries]
    assert len(paths) == len(set(paths))
    assert any(entry["quality"] == "extension_required" for entry in entries)
    assert any(entry["quality"] == "unsupported" for entry in entries)
