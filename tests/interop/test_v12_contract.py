import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from src.interop.validate import validate_document, validate_identity_semantics, validate_loss

ROOT = Path(__file__).parents[2]

def load(name): return json.loads((ROOT / name).read_text())

def test_schema_dispatch_and_separation():
    structural = load("mappings/health-connect.json")
    category = load("mappings/health-connect-exercises.json")
    identity = load("mappings/garmin-fit-exercises.json")
    ss, es, ls = (ROOT / x for x in ("interop-mapping.schema.json", "exercise-interop-mapping.schema.json", "mapping-loss.schema.json"))
    assert not validate_document(structural, ss, es, ls)
    assert not validate_document(category, ss, es, ls)
    assert not validate_document(identity, ss, es, ls)
    assert validate_document(structural, es, ss, ls)
    assert validate_document(identity, ss, ss, ls)
    unknown = copy.deepcopy(identity); unknown["mappingKind"] = "mystery"
    assert "unknown mappingKind" in validate_document(unknown, ss, es, ls)[0]

def test_crosswalk_semantics_and_relations():
    d = load("mappings/garmin-fit-exercises.json")
    ids = set(load("free-exercise-db-plusplus.json")["exercises"])
    errors, warnings = validate_identity_semantics(d, ids)
    assert not errors and not warnings
    assert {e["relation"] for e in d["entries"]} == {"exact"}

def test_loss_schema_is_separate():
    schema = ROOT / "mapping-loss.schema.json"
    loss = load("fixtures/interop/health-connect/unmapped-rir.json")["loss"]
    assert not validate_loss(loss, schema)
    assert validate_loss({"status": "unsupported", "losses": [], "unexpected": True}, schema)

def test_crosswalk_schema_rejects_wrong_shapes():
    schema = load("exercise-interop-mapping.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    identity = load("mappings/garmin-fit-exercises.json")
    bad = copy.deepcopy(identity); bad["entries"][0]["dbppExerciseIds"] = []
    assert list(validator.iter_errors(bad))
    bad = copy.deepcopy(identity); bad["entries"][0]["relation"] = "unmapped"
    assert list(validator.iter_errors(bad))

def test_duplicate_and_conflict_handling():
    d = load("mappings/garmin-fit-exercises.json")
    ids = set(load("free-exercise-db-plusplus.json")["exercises"])
    duplicate = copy.deepcopy(d); duplicate["entries"].append(copy.deepcopy(d["entries"][0]))
    assert validate_identity_semantics(duplicate, ids)[0]
    conflict = copy.deepcopy(d); conflict["entries"].append(copy.deepcopy(d["entries"][0]))
    conflict["entries"][-1]["relation"] = "broader"
    assert validate_identity_semantics(conflict, ids)[0]

def test_coverage_denominators_and_package_parity():
    report = load("reports/interop/android-health-connect.json")
    category = report["categoryCompatibility"]
    assert category["externalCovered"] == 2 and category["externalDenominator"] == 2
    identity = report["exerciseIdentityCoverage"]
    assert identity["externalToDbpp"]["denominator"] == 0
    assert identity["bidirectionalExactOrClose"]["denominator"] == 0
    for name in ("garmin-fit-exercises.json", "health-connect-exercises.json"):
        assert (ROOT / "mappings" / name).read_bytes() == (ROOT / "packages/python/fedbpp/interop_data" / name).read_bytes()

def test_registry_exposes_category_and_ambiguity():
    from src.interop.registry import MappingRegistry
    registry = MappingRegistry.load(ROOT / "mappings")
    matches = registry.lookup_external("android-health-connect", "EXERCISE_SESSION_TYPE_STRENGTH_TRAINING")
    assert len(matches) == 1 and matches[0].is_category and matches[0].is_ambiguous
    assert registry.is_ambiguous("android-health-connect", "EXERCISE_SESSION_TYPE_STRENGTH_TRAINING")

if __name__ == "__main__":
    for name in sorted(globals()):
        if name.startswith("test_"): globals()[name]()
    print("v1.2 contract tests passed")
