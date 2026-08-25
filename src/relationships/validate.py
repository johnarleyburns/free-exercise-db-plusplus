from __future__ import annotations
from collections import Counter
from typing import Any

RELATIONSHIPS = {"member_of_family", "variation_of", "equipment_variant_of", "grip_variant_of", "stance_variant_of", "angle_variant_of", "laterality_variant_of"}
DIMENSIONS = {"equipment", "grip", "stance", "angle", "laterality", "body_position", "load_position", "assistance", "resistance_type"}

def _equipment(value: str | None) -> str | None:
    if value is None: return None
    return {"body only":"bodyweight", "e-z curl bar":"ez_bar", "kettlebells":"kettlebell"}.get(value, value.replace(" ", "_"))

def validate_relationship_document(document: dict[str, Any], db: dict[str, Any]) -> list[str]:
    errors=[]; exercise_records=db.get("exercises", {}); exercises=set(exercise_records); families=document.get("families", {})
    metadata=document.get("metadata", {})
    if set(metadata.get("relationshipVocabulary", ())) != RELATIONSHIPS: errors.append("relationship vocabulary metadata mismatch")
    if set(metadata.get("dimensionVocabulary", ())) != DIMENSIONS: errors.append("dimension vocabulary metadata mismatch")
    if metadata.get("sourceSha256") != db.get("metadata", {}).get("upstream", {}).get("sha256"): errors.append("source upstream SHA-256 mismatch")
    if len(families) != len(set(families)): errors.append("duplicate family IDs")
    aliases={}
    for key, family in families.items():
        if family.get("familyId") != key: errors.append(f"family key mismatch: {key}")
        for alias in family.get("aliases",()):
            normalized=alias.casefold()
            if normalized in aliases and aliases[normalized]!=key: errors.append(f"family alias collision: {alias}")
            aliases[normalized]=key
    seen=set(); assignments={}
    for row in document.get("relationships",[]):
        if row.get("relationship")=="member_of_family":
            source=row.get("sourceExerciseId"); prior=assignments.get(source)
            if prior and prior!=row.get("familyId"): errors.append(f"contradictory family assignment: {source}")
            assignments[source]=row.get("familyId")
    for row in document.get("relationships", []):
        source=row.get("sourceExerciseId"); target=row.get("targetExerciseId")
        if source not in exercises: errors.append(f"unknown source exerciseId: {source}")
        if target is not None and target not in exercises: errors.append(f"unknown target exerciseId: {target}")
        if row.get("familyId") not in families: errors.append(f"unknown familyId: {row.get('familyId')}")
        if row.get("relationship") not in RELATIONSHIPS: errors.append(f"invalid relationship: {row.get('relationship')}")
        if row.get("confidence") not in {"high", "medium"}: errors.append(f"invalid confidence: {row.get('confidence')}")
        if row.get("relationship") != "member_of_family" and source == target: errors.append(f"self relationship: {source}")
        if row.get("relationship") == "member_of_family" and target is not None: errors.append(f"member relationship has target: {source}")
        key=(source,target,row.get("relationship"),row.get("familyId"))
        if key in seen: errors.append(f"duplicate relationship: {key}")
        seen.add(key)
        if not row.get("provenance"): errors.append(f"missing provenance: {source}")
        for dim in row.get("dimensions", {}):
            if dim not in DIMENSIONS: errors.append(f"invalid dimension: {dim}")
        if row.get("relationship") == "member_of_family":
            expected=_equipment(exercise_records.get(source, {}).get("source", {}).get("equipment"))
            actual=row.get("dimensions", {}).get("equipment")
            if expected is not None and actual != expected: errors.append(f"equipment contradiction: {source}: {actual!r} != {expected!r}")
        elif target is not None:
            source_family=assignments.get(source); target_family=assignments.get(target)
            if source_family and target_family and source_family != target_family: errors.append(f"cross-family variation edge: {source} -> {target}")
    ordered=sorted(document.get("relationships", []), key=lambda x:(x.get("relationship", ""),x.get("familyId", ""),x.get("sourceExerciseId", ""),x.get("targetExerciseId", "")))
    if document.get("relationships", []) != ordered: errors.append("relationships are not deterministically ordered")
    return errors

__all__=["validate_relationship_document"]
