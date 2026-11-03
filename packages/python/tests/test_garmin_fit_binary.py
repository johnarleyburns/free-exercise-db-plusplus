"""Binary Garmin FIT regression tests (run with the optional ``fit`` extra)."""
import json
import subprocess
import sys
from pathlib import Path

from fedbpp import ConversionError, export_garmin_fit, import_garmin_fit


ROOT = Path(__file__).parents[3]


def _workout():
    return {
        "schemaVersion": "0.3.0", "sessionId": "fit-python-test",
        "startTime": "2026-11-02T18:30:00Z", "endTime": "2026-11-02T19:15:00Z",
        "exercises": [{
            "exerciseId": "Barbell_Bench_Press", "order": 1,
            "sets": [{"setNumber": 1, "setType": "working", "reps": 8,
                      "load": {"value": 100, "unit": "kg"}, "completed": True,
                      "notes": "UTF-8 sidecar: café 💪"}],
        }],
    }


def test_binary_fit_round_trip_is_lossless_and_has_fit_header(tmp_path):
    source = _workout()
    payload = export_garmin_fit(source)
    assert payload[8:12] == b".FIT"
    path = tmp_path / "activity.fit"
    path.write_bytes(payload)
    result = import_garmin_fit(path)
    assert result.status == "lossless"
    assert result.document == source


def test_binary_fit_without_dbpp_sidecar_is_rejected_in_strict_mode():
    # A valid file whose Session omits DB++ developer fields must never be
    # reconstructed by guessing at native FIT fields.
    from garmin_fit_sdk import Encoder, FIT_EPOCH_S, Profile

    encoder = Encoder()
    encoder.write_mesg({"mesg_num": Profile["mesg_num"]["FILE_ID"], "type": "activity",
                        "manufacturer": "development", "product": 0, "time_created": FIT_EPOCH_S + 1})
    payload = bytes(encoder.close())
    try:
        import_garmin_fit(payload)
    except ConversionError as error:
        assert "sidecar" in str(error).lower()
        assert error.result is not None and error.result.status == "lossy"
    else:
        raise AssertionError("strict FIT import accepted an unreconstructible file")


def test_cli_binary_export_and_import_round_trip(tmp_path):
    source = _workout()
    input_path = tmp_path / "actual.json"
    fit_path = tmp_path / "activity.fit"
    output_path = tmp_path / "round-trip.json"
    input_path.write_text(json.dumps(source), encoding="utf-8")
    command = [sys.executable, "-m", "fedbpp.cli"]
    subprocess.run(command + ["export", "garmin-fit", str(input_path), "--binary", "--output", str(fit_path)], check=True)
    subprocess.run(command + ["import", "garmin-fit", str(fit_path), "--binary", "--output", str(output_path)], check=True)
    assert json.loads(output_path.read_text(encoding="utf-8")) == source
