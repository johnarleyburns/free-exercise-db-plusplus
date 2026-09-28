"""Loss-aware adapters for Garmin FIT, HealthKit, and Health Connect.

These adapters deliberately produce a JSON representation of each platform
record rather than pretending that a platform API or the Garmin binary SDK is
available in the offline core package.  The representation contains both the
native projection and an exact DB++ ACTUAL sidecar.  Platform bindings can use
the projection to create native records and persist the sidecar alongside the
record using the platform-specific mechanism described in the interop guide.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .conversion import ConversionError, ConversionResult
from .workout import Workout, ValidationError

HEALTH_INTEROP_VERSION = "0.1.0"
TARGETS = {"garmin-fit", "healthkit", "health-connect"}


def _fit_sdk():
    try:
        from garmin_fit_sdk import Encoder, FIT_EPOCH_S, Profile, Stream
        from garmin_fit_sdk.fit import BASE_TYPE
    except ImportError as exc:
        raise ConversionError("Garmin FIT binary support requires the optional 'garmin-fit-sdk' package") from exc
    return Encoder, FIT_EPOCH_S, Profile, Stream, BASE_TYPE


def _target(value: str) -> str:
    aliases = {
        "garmin": "garmin-fit",
        "fit": "garmin-fit",
        "health_connect": "health-connect",
        "healthconnect": "health-connect",
    }
    target = aliases.get(str(value).lower(), str(value).lower())
    if target not in TARGETS:
        raise ConversionError(f"unsupported health interop format: {value}")
    return target


def _document(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, Path)):
        path = Path(value)
        if isinstance(value, str) and value.lstrip().startswith("{"):
            return json.loads(value)
        return json.loads(path.read_text(encoding="utf-8"))
    raise ConversionError("health interop document must be a mapping, JSON document, or path")


def _workout(value: Any) -> dict[str, Any]:
    document = value.document if isinstance(value, Workout) else value
    if not isinstance(document, dict):
        raise ConversionError("DB++ workout must be an object")
    try:
        Workout.from_dict(document).validate()
    except ValidationError as exc:
        raise ConversionError(f"invalid DB++ ACTUAL: {exc}") from exc
    return document


def _canonical(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utf8_chunks(value: str, max_bytes: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for character in value:
        character_size = len(character.encode("utf-8"))
        if current and size + character_size > max_bytes:
            chunks.append("".join(current))
            current = []
            size = 0
        current.append(character)
        size += character_size
    if current or not chunks:
        chunks.append("".join(current))
    return chunks


def _number(value: Any) -> float | int | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _load_kg(item: dict[str, Any]) -> float | None:
    load = item.get("load")
    if not isinstance(load, dict) or _number(load.get("value")) is None:
        return None
    unit = str(load.get("unit", "")).lower()
    if unit == "kg":
        return float(load["value"])
    if unit in {"g", "gram", "grams"}:
        return float(load["value"]) / 1000.0
    if unit in {"lb", "lbs", "pound", "pounds"}:
        return float(load["value"]) * 0.45359237
    return None


def _set_projection(exercise: dict[str, Any], item: dict[str, Any], index: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "setNumber": item.get("setNumber", index),
        "setType": item.get("setType", "working"),
        "completed": bool(item.get("completed", False)),
    }
    for key in ("reps", "rpe", "rir", "tempo", "toFailure", "assistance", "notes"):
        if item.get(key) is not None:
            result[key] = item[key]
    if _load_kg(item) is not None:
        result["weightKg"] = _load_kg(item)
    if isinstance(item.get("duration"), dict):
        result["durationSeconds"] = item["duration"].get("value") if item["duration"].get("unit") in {"s", "sec", "seconds"} else None
    if isinstance(item.get("distance"), dict):
        result["distanceMeters"] = item["distance"].get("value") if item["distance"].get("unit") in {"m", "meter", "meters"} else None
    return result


def _fit_projection(workout: dict[str, Any]) -> dict[str, Any]:
    laps: list[dict[str, Any]] = []
    for exercise in workout.get("exercises", []):
        for index, item in enumerate(exercise.get("sets", []), 1):
            laps.append({
                "exerciseId": exercise.get("exerciseId"),
                "exerciseName": exercise.get("exerciseName"),
                "laterality": exercise.get("laterality"),
                "structure": exercise.get("structure"),
                "set": _set_projection(exercise, item, index),
            })
    return {
        "fileType": "activity",
        "fileId": {"type": "activity", "timeCreated": workout["startTime"], "number": workout["sessionId"]},
        "session": {
            "startTime": workout["startTime"],
            "endTime": workout.get("endTime"),
            "sport": "strength_training",
            "totalElapsedTimeSeconds": None,
        },
        "laps": laps,
        "developerData": {
            "namespace": "org.free-exercise-db-plusplus",
            "canonicalWorkoutJSON": _canonical(workout),
            "schemaVersion": workout.get("schemaVersion"),
        },
    }


def _healthkit_projection(workout: dict[str, Any]) -> dict[str, Any]:
    return {
        "workoutActivityType": "traditionalStrengthTraining",
        "startDate": workout["startTime"],
        "endDate": workout.get("endTime"),
        "durationSeconds": None,
        "metadata": {
            "org.free-exercise-db-plusplus.sessionId": workout["sessionId"],
            "org.free-exercise-db-plusplus.schemaVersion": workout.get("schemaVersion"),
            "org.free-exercise-db-plusplus.canonicalWorkoutJSON": _canonical(workout),
        },
        "samples": [],
    }


def _health_connect_projection(workout: dict[str, Any]) -> dict[str, Any]:
    segments: list[dict[str, Any]] = []
    for exercise in workout.get("exercises", []):
        for index, item in enumerate(exercise.get("sets", []), 1):
            segment: dict[str, Any] = {
                "exerciseType": "strength_training",
                "exerciseId": exercise.get("exerciseId"),
                "exerciseName": exercise.get("exerciseName"),
                "startTime": workout["startTime"],
                "endTime": workout.get("endTime") or workout["startTime"],
                "repetitions": item.get("reps"),
                "weightKg": _load_kg(item),
                "setIndex": item.get("setNumber", index),
                "rateOfPerceivedExertion": item.get("rpe"),
            }
            segments.append(segment)
    return {
        "startTime": workout["startTime"],
        "endTime": workout.get("endTime"),
        "exerciseType": "strength_training",
        "metadata": {
            "clientRecordId": workout["sessionId"],
            "clientRecordVersion": 1,
            "org.free-exercise-db-plusplus.canonicalWorkoutJSON": _canonical(workout),
            "org.free-exercise-db-plusplus.schemaVersion": workout.get("schemaVersion"),
        },
        "segments": segments,
    }


def _projection(target: str, workout: dict[str, Any]) -> dict[str, Any]:
    if target == "garmin-fit":
        return _fit_projection(workout)
    if target == "healthkit":
        return _healthkit_projection(workout)
    return _health_connect_projection(workout)


def export_garmin_fit(workout: Any) -> bytes:
    """Encode a DB++ ACTUAL as a Garmin FIT Activity file.

    The optional official Garmin SDK is used for binary encoding. The exact
    canonical workout is chunked into FIT string developer fields on Session;
    standard File Id/Device Info/Event/Lap/Session/Activity messages provide a
    valid native Activity projection.
    """
    Encoder, fit_epoch, Profile, _, base_type = _fit_sdk()
    document = _workout(workout)
    from datetime import datetime, timezone

    def timestamp(value: Any) -> int:
        if not isinstance(value, str):
            raise ConversionError("FIT export requires ISO-8601 startTime")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ConversionError(f"invalid workout timestamp: {value}") from exc
        if parsed.tzinfo is None:
            raise ConversionError("FIT export requires an offset-aware timestamp")
        return int(parsed.astimezone(timezone.utc).timestamp()) - fit_epoch

    start = timestamp(document["startTime"])
    end = timestamp(document.get("endTime") or document["startTime"])
    elapsed = max(0, end - start)
    canonical = _canonical(document)
    chunks = _utf8_chunks(canonical, 200)
    developer_id = {"developer_data_index": 0, "application_id": [70, 69, 68, 66, 80, 80, 45, 72, 69, 65, 76, 84, 72, 45, 49, 0], "application_version": 1}
    descriptions = {}
    for index in range(len(chunks)):
        descriptions[index] = {
            "developer_data_id_mesg": developer_id,
            "field_description_mesg": {"developer_data_index": 0, "field_definition_number": index,
                                        "fit_base_type_id": base_type["STRING"],
                                        "field_name": f"DBPP JSON {index:03d}", "units": "json",
                                        "native_mesg_num": Profile["mesg_num"]["SESSION"]},
        }
    mesgs = [
        {"mesg_num": Profile["mesg_num"]["DEVELOPER_DATA_ID"], **developer_id},
        *({"mesg_num": Profile["mesg_num"]["FIELD_DESCRIPTION"], **d["field_description_mesg"]} for d in descriptions.values()),
        {"mesg_num": Profile["mesg_num"]["FILE_ID"], "type": "activity", "manufacturer": "development", "product": 0, "time_created": start, "serial_number": _stable_serial(document["sessionId"])},
        {"mesg_num": Profile["mesg_num"]["DEVICE_INFO"], "device_index": "creator", "manufacturer": "development", "product": 0, "product_name": "FEDB++", "serial_number": _stable_serial(document["sessionId"]), "software_version": 1.0, "timestamp": start},
        {"mesg_num": Profile["mesg_num"]["EVENT"], "timestamp": start, "event": "timer", "event_type": "start"},
        {"mesg_num": Profile["mesg_num"]["LAP"], "message_index": 0, "timestamp": end, "start_time": start, "total_elapsed_time": elapsed, "total_timer_time": elapsed},
        {"mesg_num": Profile["mesg_num"]["SESSION"], "message_index": 0, "timestamp": end, "start_time": start, "total_elapsed_time": elapsed, "total_timer_time": elapsed, "sport": "fitness_equipment", "sub_sport": "strength_training", "first_lap_index": 0, "num_laps": 1, "developer_fields": {index: chunk for index, chunk in enumerate(chunks)}},
        {"mesg_num": Profile["mesg_num"]["EVENT"], "timestamp": end, "event": "timer", "event_type": "stop"},
        {"mesg_num": Profile["mesg_num"]["ACTIVITY"], "timestamp": end, "num_sessions": 1, "local_timestamp": end, "total_timer_time": elapsed},
    ]
    encoder = Encoder(field_descriptions=descriptions)
    for message in mesgs:
        encoder.write_mesg(message)
    return bytes(encoder.close())


def _stable_serial(value: str) -> int:
    result = 2166136261
    for byte in str(value).encode("utf-8"):
        result = ((result ^ byte) * 16777619) & 0xFFFFFFFF
    return result or 1


def import_garmin_fit(data: bytes | bytearray | str | Path, *, mode: str = "strict") -> ConversionResult:
    """Decode a Garmin FIT Activity file using the optional official SDK."""
    _, _, _, Stream, _ = _fit_sdk()
    if isinstance(data, (str, Path)):
        raw = Path(data).read_bytes()
    else:
        raw = bytes(data)
    from garmin_fit_sdk import Decoder
    stream = Stream.from_byte_array(bytearray(raw))
    decoder = Decoder(stream)
    if not decoder.is_fit():
        raise ConversionError("input is not a FIT file")
    messages, errors = decoder.read()
    if errors:
        raise ConversionError(f"FIT decoder reported errors: {errors}")
    chunks: list[tuple[int, str]] = []
    for session in messages.get("session_mesgs", []):
        for key, value in (session.get("developer_fields") or {}).items():
            if isinstance(key, int) and isinstance(value, str):
                chunks.append((key, value))
    if not chunks:
        result = ConversionResult({}, "lossy", ({"path": "session_mesgs.developer_fields", "reason": "FIT file has no DB++ canonical sidecar", "destination": "full DB++ ACTUAL"},), (), {"target": "garmin-fit"}, "garmin-fit", "dbpp-actual")
        if mode == "strict":
            raise ConversionError("strict FIT import refused information loss", result=result)
        raise ConversionError("FIT import without a DB++ sidecar is not reconstructible", result=result)
    raw_json = "".join(value for _, value in sorted(chunks))
    try:
        document = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ConversionError("FIT DB++ developer sidecar is invalid JSON") from exc
    result = ConversionResult(document, "lossless", (), (), {"target": "garmin-fit"}, "garmin-fit", "dbpp-actual")
    try:
        Workout.from_dict(document).validate()
    except ValidationError as exc:
        raise ConversionError(f"FIT sidecar contains invalid DB++ ACTUAL: {exc}", result=result) from exc
    return result


def export_health_workout(target: str, workout: Any, *, mode: str = "strict") -> ConversionResult:
    """Export a DB++ ACTUAL to a loss-aware native projection envelope.

    The exact DB++ JSON is embedded as a sidecar.  A native platform adapter
    must persist that sidecar with the created record to claim lossless export.
    """
    if mode not in {"strict", "allow-lossy"}:
        raise ValueError("mode must be 'strict' or 'allow-lossy'")
    target = _target(target)
    document = _workout(workout)
    output = {
        "interopVersion": HEALTH_INTEROP_VERSION,
        "target": target,
        "recordId": document["sessionId"],
        "canonicalWorkout": document,
        "projection": _projection(target, document),
        "fidelity": "lossless_with_sidecar",
        "losses": [],
        "warnings": ["Persist canonicalWorkout with the native record; target APIs do not represent every DB++ field."],
    }
    return ConversionResult(output, "lossless", (), tuple(output["warnings"]),
                            {"target": target, "interopVersion": HEALTH_INTEROP_VERSION},
                            "dbpp-actual", target)


def _canonical_from_external(document: dict[str, Any]) -> dict[str, Any] | None:
    value = document.get("canonicalWorkout")
    if isinstance(value, dict):
        return value
    projection = document.get("projection")
    if isinstance(projection, dict):
        for container in (projection, projection.get("metadata"), projection.get("developerData")):
            if not isinstance(container, dict):
                continue
            raw = container.get("org.free-exercise-db-plusplus.canonicalWorkoutJSON") or container.get("canonicalWorkoutJSON")
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
    return None


def _lossy_import(target: str, document: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    projection = document.get("projection") if isinstance(document.get("projection"), dict) else document
    losses = [{"path": "canonicalWorkout", "reason": "native record has no DB++ sidecar", "destination": "full DB++ ACTUAL"}]
    if target == "healthkit":
        start = projection.get("startDate")
        end = projection.get("endDate")
        workout = {"schemaVersion": "0.3.0", "sessionId": str(document.get("recordId") or "healthkit-session"), "startTime": start, "endTime": end, "source": {"system": "healthkit", "recordId": str(document.get("recordId") or "healthkit-session")}, "exercises": []}
        losses.append({"path": "projection", "reason": "HealthKit has no standard per-set exercise identity/load/RPE representation", "destination": "DB++ exercises"})
        return workout, losses
    rows = projection.get("laps", []) if target == "garmin-fit" else projection.get("segments", [])
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        row = row if isinstance(row, dict) else {}
        source = row.get("set") if target == "garmin-fit" else row
        source = source if isinstance(source, dict) else {}
        exercise_id = row.get("exerciseId")
        key = str(exercise_id or row.get("exerciseName") or source.get("exerciseName") or "custom:unknown")
        exercise = grouped.setdefault(key, {"exerciseId": exercise_id, "exerciseName": None if exercise_id else (row.get("exerciseName") or source.get("exerciseName") or key), "order": len(grouped) + 1, "sets": []})
        item = {"setNumber": source.get("setNumber") or source.get("setIndex") or len(exercise["sets"]) + 1, "setType": source.get("setType", "working"), "completed": bool(source.get("completed", True))}
        if source.get("reps") is not None:
            item["reps"] = source["reps"]
        if source.get("weightKg") is not None:
            item["load"] = {"value": source["weightKg"], "unit": "kg"}
        if source.get("rpe") is not None or source.get("rateOfPerceivedExertion") is not None:
            item["rpe"] = source.get("rpe", source.get("rateOfPerceivedExertion"))
        exercise["sets"].append(item)
    start = projection.get("startTime") or projection.get("session", {}).get("startTime")
    end = projection.get("endTime") or projection.get("session", {}).get("endTime")
    workout = {"schemaVersion": "0.3.0", "sessionId": str(document.get("recordId") or "external-session"), "startTime": start, "endTime": end, "source": {"system": target, "recordId": str(document.get("recordId") or "external-session")}, "exercises": list(grouped.values())}
    return workout, losses


def import_health_workout(target: str, external_document: Any, *, mode: str = "strict") -> ConversionResult:
    """Import a native projection or an envelope produced by this module."""
    if mode not in {"strict", "allow-lossy"}:
        raise ValueError("mode must be 'strict' or 'allow-lossy'")
    target = _target(target)
    if target == "garmin-fit" and (isinstance(external_document, (bytes, bytearray)) or (isinstance(external_document, (str, Path)) and str(external_document).lower().endswith(".fit"))):
        return import_garmin_fit(external_document, mode=mode)
    document = _document(external_document)
    canonical = _canonical_from_external(document)
    if canonical is not None:
        output = canonical
        losses: list[dict[str, str]] = []
        status = "lossless"
    else:
        output, losses = _lossy_import(target, document)
        status = "lossy"
    result = ConversionResult(output, status, tuple(losses), (), {"target": target, "interopVersion": HEALTH_INTEROP_VERSION}, target, "dbpp-actual")
    if losses and mode == "strict":
        raise ConversionError("strict health import refused information loss", result=result)
    try:
        Workout.from_dict(output).validate()
    except ValidationError as exc:
        raise ConversionError(f"imported DB++ ACTUAL is invalid: {exc}", result=result) from exc
    return result


__all__ = ["HEALTH_INTEROP_VERSION", "TARGETS", "export_health_workout", "import_health_workout", "export_garmin_fit", "import_garmin_fit"]
