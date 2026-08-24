import json
from pathlib import Path
ROOT = Path(__file__).parents[2]
def test_healthkit_mapping_registry():
    mapping = json.loads((ROOT / "mappings/healthkit.json").read_text())
    assert mapping["target"] == "apple-healthkit"
    assert mapping["mappingVersion"] == "0.1.0"
    entries = mapping["entries"]
    assert len(entries) >= 10
    allowed = {"exact", "compatible", "lossy", "extension_required", "unsupported"}
    assert {e["quality"] for e in entries} <= allowed
    assert len({(e["sourcePath"], e["targetField"]) for e in entries}) == len(entries)
    assert any(e["quality"] == "unsupported" for e in entries)
    assert any(e["quality"] == "extension_required" for e in entries)
