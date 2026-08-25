"""Strict, deterministic validation for v1.2 mapping artifact classes."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

KINDS={"field":"structural","structural":"structural","category":"structural","identity":"identity"}

def _validator(path):
    schema=json.loads(Path(path).read_text()); Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema,format_checker=FormatChecker())

def validate_document(document,structural_schema,identity_schema,loss_schema,*,source="mapping"):
    kind=document.get("mappingKind")
    if kind not in KINDS: return [f"{source}: unknown mappingKind: {kind!r}"]
    schema={"structural":structural_schema,"identity":identity_schema,"loss":loss_schema}[KINDS[kind]]
    return [f"{source}: {e.message}" for e in _validator(schema).iter_errors(document)]

def _record_key(e):
    return (e.get("externalId"),e.get("externalName"),e.get("relation"),e.get("direction"),tuple(e.get("dbppExerciseIds",[])))

def validate_identity_semantics(document,ids,*,source="mapping"):
    errors=[]; warnings=[]; seen=set(); records=document.get("entries",[])
    for e in records:
        key=_record_key(e)
        if key in seen: errors.append(f"{source}: duplicate exact record {key[0]}")
        seen.add(key)
        if e.get("relation")=="unmapped": warnings.append(f"{source}: unmapped {e.get('externalId')}")
        for exercise_id in e.get("dbppExerciseIds",[]):
            if exercise_id not in ids: errors.append(f"{source}: unknown DB++ exerciseId {exercise_id}")
    by_external={}
    for e in records: by_external.setdefault(e.get("externalId"),[]).append(e)
    for external_id,group in by_external.items():
        exact_targets=[tuple(e.get("dbppExerciseIds",[])) for e in group if e.get("relation")=="exact"]
        if len(set(exact_targets)) > 1:
            errors.append(f"{source}: contradictory exact records for {external_id}")
        edges={}
        for e in group:
            edge=(tuple(e.get("dbppExerciseIds",[])),e.get("direction"))
            if edge in edges and edges[edge] != e.get("relation"):
                errors.append(f"{source}: contradictory relations for {external_id}")
            edges[edge]=e.get("relation")
    return errors,warnings

def validate_loss(document,loss_schema,*,source="loss"):
    return [f"{source}: {e.message}" for e in _validator(loss_schema).iter_errors(document)]

def validate_family_mapping(document,family_schema,relationship_document,*,source="family mapping"):
    errors=[f"{source}: {e.message}" for e in _validator(family_schema).iter_errors(document)]
    families=set(relationship_document.get("families",{})); seen=set()
    for entry in document.get("entries",[]):
        key=(entry.get("externalId"),entry.get("familyId"),entry.get("direction"))
        if key in seen: errors.append(f"{source}: duplicate family mapping {key}")
        seen.add(key)
        if entry.get("familyId") not in families: errors.append(f"{source}: unknown familyId {entry.get('familyId')}")
    return errors

def validate_all(mapping_dir,db_path,schema_path,crosswalk_schema_path,loss_schema_path=None):
    ids=set(json.loads(Path(db_path).read_text())["exercises"]); errors=[]; warnings=[]
    for path in sorted(Path(mapping_dir).glob("*.json")):
        document=json.loads(path.read_text())
        # Family mappings use their independent schema and are validated by
        # the v1.5 relationship CI step; preserve v1.2 dispatch semantics.
        if document.get("mappingKind") == "family":
            continue
        errors.extend(validate_document(document,schema_path,crosswalk_schema_path,loss_schema_path or schema_path,source=str(path)))
        if document.get("mappingKind")=="identity":
            e,w=validate_identity_semantics(document,ids,source=str(path)); errors.extend(e); warnings.extend(w)
    return errors,warnings
