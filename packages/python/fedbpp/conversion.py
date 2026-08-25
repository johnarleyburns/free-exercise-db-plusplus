"""Deterministic, strict-by-default workout conversion API."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .interop import MappingMatch, MappingRegistry
from .workout import Workout, ValidationError

ADAPTER_VERSION = "1.3.0"
FHIR_SYSTEM = "https://free-exercise-db-plusplus.org/fhir/exercise"


@dataclass(frozen=True)
class ConversionResult:
    document: Any
    status: str
    losses: tuple[dict[str, str], ...] = ()
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    source_format: str = ""
    destination_format: str = ""
    adapter_version: str = ADAPTER_VERSION

    @property
    def output(self) -> Any:
        return self.document

    def report(self) -> dict[str, Any]:
        result = {"status": self.status, "losses": list(self.losses)}
        if self.warnings:
            result["warnings"] = list(self.warnings)
        if self.provenance:
            result["provenance"] = self.provenance
        return result


class ConversionError(ValueError):
    """A conversion failed validation or strict loss policy."""
    def __init__(self, message: str, *, result: ConversionResult | None = None):
        super().__init__(message)
        self.result = result


def _mode(mode: str) -> str:
    if mode not in {"strict", "allow-lossy"}:
        raise ValueError("mode must be 'strict' or 'allow-lossy'")
    return mode


def _status(losses: list[dict[str, str]], normalizations: list[str]) -> str:
    if losses:
        return "lossy"
    return "normalized" if normalizations else "lossless"


def _read(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        if isinstance(value, str) and value.lstrip().startswith("{"):
            return json.loads(value)
        return json.loads(value if isinstance(value, (bytes, bytearray)) else Path(value).read_text(encoding="utf-8"))
    raise ConversionError("external document must be a mapping, JSON document, or path")


def _quantity(value: Any, unit: str | None = None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not isinstance(value.get("value"), (int, float)):
        raise ConversionError("quantity must contain a numeric value")
    return {"value": value["value"], "unit": unit or value.get("unit", "")}


def _fhir_input(document: dict[str, Any], mode: str, registry: MappingRegistry) -> ConversionResult:
    if document.get("resourceType") != "Bundle" or document.get("type") not in {"collection", "transaction"}:
        raise ConversionError("FHIR input must be a collection or transaction Bundle")
    entries = document.get("entry")
    if not isinstance(entries, list):
        raise ConversionError("FHIR Bundle.entry must be an array")
    observations = [e.get("resource") for e in entries if isinstance(e, dict) and isinstance(e.get("resource"), dict)]
    if len(observations) != len(entries):
        raise ConversionError("each FHIR Bundle entry must contain a resource")
    session_id = ((document.get("identifier") or {}).get("value") or "fhir-" + str(document.get("id") or "bundle"))
    start = document.get("timestamp")
    if not isinstance(start, str):
        raise ConversionError("FHIR Bundle.timestamp is required")
    losses: list[dict[str, str]] = []
    warnings: list[str] = []
    normalizations: list[str] = []
    exercises: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, Any]] = {}
    for index, resource in enumerate(observations, 1):
        if resource.get("resourceType") != "Observation":
            raise ConversionError("FHIR Bundle contains a non-Observation resource")
        coding = ((resource.get("code") or {}).get("coding") or [])
        coding = next((c for c in coding if isinstance(c, dict) and c.get("code")), None)
        if not coding:
            raise ConversionError(f"Observation {index} has no exercise coding")
        external_id = str(coding["code"])
        matches = registry.lookup_external("fhir", external_id)
        exact = [m for m in matches if m.relation == "exact" and m.direction in {"external_to_dbpp", "bidirectional"}]
        if len(exact) != 1:
            if len(exact) > 1 or any(m.is_ambiguous for m in matches):
                reason = "ambiguous exercise identity mapping"
            else:
                reason = "no reviewed exact exercise identity mapping"
            losses.append({"path": f"entry[{index - 1}].resource.code", "reason": reason, "destination": "DB++ exerciseId"})
            exercise_id = None
            name = coding.get("display") or external_id
            key = f"custom:{external_id}"
        else:
            match = exact[0]
            exercise_id = match.dbpp_exercise_id
            name = None
            key = exercise_id
        target = grouped.get(key)
        if target is None:
            target = {"exerciseId": exercise_id, "exerciseName": name, "order": len(grouped) + 1,
                      "externalExerciseId": {"system": "fhir", "value": external_id},
                      "interop": {"mappingVersion": "0.1.0", "adapterVersion": ADAPTER_VERSION,
                                   "relation": exact[0].relation if exact else "unmapped",
                                   "direction": exact[0].direction if exact else "external_to_dbpp",
                                   "confidence": exact[0].confidence if exact else "none"}, "sets": []}
            if exercise_id is None:
                target["exerciseName"] = name
            grouped[key] = target
        components = {}
        for component in resource.get("component", []):
            if not isinstance(component, dict):
                continue
            key = str(component.get("code", {}).get("text", ""))
            components[key] = component.get("valueQuantity", component.get("valueInteger", component.get("valueCodeableConcept")))
        value = resource.get("valueQuantity") or {}
        reps = value.get("value")
        if reps is not None and (not isinstance(reps, int) or reps < 0):
            raise ConversionError(f"Observation {index} reps must be a non-negative integer")
        load = components.get("load")
        if load:
            load = _quantity(load)
            if load["unit"] in {"lb", "lbs", "pound", "pounds"}:
                load = {"value": load["value"] * 0.45359237, "unit": "kg"}
                normalizations.append(f"entry[{index - 1}].component.load: lb to kg")
        completed = resource.get("status", "final") in {"final", "amended"}
        set_number_value = components.get("setNumber")
        if isinstance(set_number_value, dict):
            set_number_value = set_number_value.get("value", len(target["sets"]) + 1)
        set_type_value = components.get("setType")
        if isinstance(set_type_value, dict):
            set_type_value = ((set_type_value.get("coding") or [{}])[0].get("code") or "working")
        target["sets"].append({"setNumber": int(set_number_value or len(target["sets"]) + 1),
                               "setType": set_type_value or "working",
                               "reps": int(reps) if reps is not None else None, "load": load,
                               "completed": completed})
    output = {"schemaVersion": "0.3.0", "sessionId": str(session_id), "startTime": start,
              "endTime": document.get("meta", {}).get("lastUpdated") if isinstance(document.get("meta"), dict) else None,
              "source": {"system": "fhir", "version": "R4 / US Physical Activity IG 1.0.0 STU1",
                         "recordId": str(document.get("id") or session_id), "mappingVersion": "0.1.0",
                         "adapterVersion": ADAPTER_VERSION}, "exercises": list(grouped.values())}
    result = ConversionResult(output, _status(losses, normalizations), tuple(losses), tuple(warnings), output["source"], "fhir", "dbpp-actual")
    if losses and mode == "strict":
        raise ConversionError("strict import refused information loss", result=result)
    try:
        Workout.from_dict(output).validate()
    except (ValidationError, KeyError) as exc:
        raise ConversionError(f"generated DB++ ACTUAL is invalid: {exc}", result=result) from exc
    return result


def _fhir_output(workout: Any, mode: str, registry: MappingRegistry) -> ConversionResult:
    document = workout.document if isinstance(workout, Workout) else workout
    try:
        Workout.from_dict(document).validate()
    except Exception as exc:
        raise ConversionError(f"invalid DB++ ACTUAL: {exc}") from exc
    losses: list[dict[str, str]] = []
    warnings: list[str] = []
    entries = []
    for ei, exercise in enumerate(document["exercises"]):
        external_id = None
        match: MappingMatch | None = None
        if exercise.get("exerciseId"):
            matches = registry.lookup_dbpp(exercise["exerciseId"], "fhir")
            exact = [m for m in matches if m.relation == "exact" and m.direction in {"dbpp_to_external", "bidirectional"}]
            if len(exact) == 1:
                match = exact[0]; external_id = match.external_id
            else:
                losses.append({"path": f"exercises[{ei}].exerciseId", "reason": "no reviewed exact FHIR identity mapping", "destination": "FHIR exercise coding"})
        if external_id is None:
            external_id = (exercise.get("externalExerciseId") or {}).get("value") or "custom:" + str(exercise.get("exerciseName") or "unknown")
            warnings.append(f"exercises[{ei}]: exported as custom/unmapped coding")
        for si, item in enumerate(exercise.get("sets", []), 1):
            components = [{"code": {"text": "setNumber"}, "valueInteger": item.get("setNumber", si)},
                          {"code": {"text": "setType"}, "valueCodeableConcept": {"coding": [{"code": item.get("setType", "working")}]}}]
            if item.get("load"):
                load = dict(item["load"])
                if load.get("unit") in {"lb", "lbs"}:
                    load["value"] *= 0.45359237; load["unit"] = "kg"
                    warnings.append(f"exercises[{ei}].sets[{si - 1}].load: lb to kg")
            if item.get("load"):
                components.append({"code": {"text": "load"}, "valueQuantity": load})
            for field in ("rpe", "rir", "tempo", "restAfter", "duration", "distance"):
                if item.get(field) is not None:
                    warnings.append(f"exercises[{ei}].sets[{si - 1}].{field}: preserved only by DB++ extension policy")
            resource = {"resourceType": "Observation", "id": f"set-{ei + 1:04d}-{si:04d}", "status": "final" if item.get("completed") else "preliminary",
                        "code": {"coding": [{"system": FHIR_SYSTEM, "code": external_id, "display": exercise.get("exerciseName") or exercise.get("exerciseId") or external_id}]},
                        "component": components}
            if item.get("reps") is not None:
                resource["valueQuantity"] = {"value": item["reps"], "unit": "{repetitions}"}
            entries.append({"fullUrl": f"urn:uuid:{resource['id']}", "resource": resource})
    source = document.get("source") or {}
    bundle = {"resourceType": "Bundle", "type": "collection", "identifier": {"value": document["sessionId"]},
              "timestamp": document["startTime"], "entry": entries,
              "meta": {"tag": [{"system": "https://free-exercise-db-plusplus.org", "code": "dbpp-actual"}]}}
    result = ConversionResult(bundle, _status(losses, warnings), tuple(losses), tuple(warnings), source, "dbpp-actual", "fhir")
    if losses and mode == "strict":
        raise ConversionError("strict export refused information loss", result=result)
    return result


def import_workout(format: str, external_document: Any, *, mode: str = "strict", registry: MappingRegistry | None = None) -> ConversionResult:
    _mode(mode); registry = registry or MappingRegistry.load()
    if format.lower() == "fhir":
        try: return _fhir_input(_read(external_document), mode, registry)
        except ConversionError: raise
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc: raise ConversionError(f"invalid FHIR input: {exc}") from exc
    raise ConversionError(f"unsupported import format: {format}")


def export_workout(format: str, workout: Any, *, mode: str = "strict", registry: MappingRegistry | None = None) -> ConversionResult:
    _mode(mode); registry = registry or MappingRegistry.load()
    if format.lower() == "fhir": return _fhir_output(workout, mode, registry)
    raise ConversionError(f"unsupported export format: {format}")


__all__ = ["ConversionError", "ConversionResult", "import_workout", "export_workout", "ADAPTER_VERSION"]
