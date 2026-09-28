import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "packages/python"))
from fedbpp import ConversionError, export_workout, import_workout


def fhir(code="Dumbbell_Bench_Press", unit="kg", value=80):
    return {"resourceType": "Bundle", "type": "collection", "id": "b", "identifier": {"value": "s"},
            "timestamp": "2026-08-24T14:00:00Z", "entry": [{"resource": {
                "resourceType": "Observation", "status": "final",
                "code": {"coding": [{"system": "https://free-exercise-db-plusplus.org/fhir/exercise", "code": code}]},
                "valueQuantity": {"value": 8, "unit": "{repetitions}"},
                "component": [{"code": {"text": "load"}, "valueQuantity": {"value": value, "unit": unit}}]}}]}


def test_fhir_exact_import_export_is_deterministic():
    a = import_workout("fhir", fhir())
    b = import_workout("fhir", fhir())
    assert a.status == "lossless" and a.document == b.document
    assert a.document["source"]["adapterVersion"] == "1.3.0"
    exported = export_workout("fhir", a.document)
    assert exported.status == "lossless"
    assert exported.document == export_workout("fhir", a.document).document


def test_lb_normalization_is_not_loss():
    result = import_workout("fhir", fhir(unit="lb", value=100))
    assert result.status == "normalized"
    assert result.document["exercises"][0]["sets"][0]["load"]["unit"] == "kg"
    assert not result.losses


def test_unknown_identity_survives_only_in_lossy_mode():
    with_error = False
    try:
        import_workout("fhir", fhir("unknown-exercise"))
    except ConversionError as exc:
        with_error = exc.result.status == "lossy"
    assert with_error
    result = import_workout("fhir", fhir("unknown-exercise"), mode="allow-lossy")
    exercise = result.document["exercises"][0]
    assert exercise["exerciseId"] is None and exercise["exerciseName"] == "unknown-exercise"
    assert exercise["externalExerciseId"]["value"] == "unknown-exercise"
    assert result.losses


def test_malformed_fhir_rejected():
    try:
        import_workout("fhir", {"resourceType": "Patient"})
    except ConversionError:
        return
    raise AssertionError("malformed FHIR must be rejected")


def test_invalid_actual_rejected():
    try:
        export_workout("fhir", {"schemaVersion": "0.3.0"})
    except ConversionError:
        return
    raise AssertionError("invalid ACTUAL must be rejected")


def test_health_targets_round_trip_full_actual_through_sidecar():
    workout = {
        "schemaVersion": "0.3.0", "sessionId": "health-session",
        "startTime": "2026-08-24T14:00:00Z", "endTime": "2026-08-24T15:00:00Z",
        "exercises": [{"exerciseId": "Dumbbell_Bench_Press", "order": 1, "laterality": "bilateral", "sets": [{
            "setNumber": 1, "setType": "working", "reps": 8,
            "load": {"value": 80, "unit": "kg"}, "rpe": 8, "rir": 2,
            "completed": True, "tempo": "3010", "toFailure": False,
            "repetitions": [{"repNumber": 1, "meanVelocity": {"value": 0.4, "unit": "m/s"}}]
        }]}]
    }
    for target in ("garmin-fit", "healthkit", "health-connect"):
        exported = export_workout(target, workout)
        assert exported.status == "lossless"
        assert exported.document["fidelity"] == "lossless_with_sidecar"
        imported = import_workout(target, exported.document)
        assert imported.status == "lossless"
        assert imported.document == workout


def test_health_native_only_import_is_rejected_in_strict_mode():
    try:
        import_workout("healthkit", {"recordId": "hk-1", "projection": {"startDate": "2026-08-24T14:00:00Z"}})
    except ConversionError as exc:
        assert exc.result is not None and exc.result.status == "lossy"
        return
    raise AssertionError("native-only HealthKit import must fail in strict mode")
