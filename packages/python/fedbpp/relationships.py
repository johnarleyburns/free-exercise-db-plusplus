"""Optional descriptive exercise-family and relationship API."""
from __future__ import annotations
from dataclasses import dataclass
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class Family:
    family_id: str
    name: str
    aliases: tuple[str, ...]

@dataclass(frozen=True)
class Relationship:
    source_exercise_id: str
    family_id: str
    relationship: str
    dimensions: dict[str, Any]
    confidence: str
    target_exercise_id: str | None = None
    provenance: tuple[dict[str, Any], ...] = ()

class RelationshipRegistry:
    def __init__(self, document: dict[str, Any], db: Any | None = None):
        self.document, self.db = document, db
        self._families = {k: Family(k, v["name"], tuple(v.get("aliases", ()))) for k, v in document.get("families", {}).items()}
        self._rows = tuple(Relationship(r["sourceExerciseId"], r["familyId"], r["relationship"], dict(r.get("dimensions", {})), r["confidence"], r.get("targetExerciseId"), tuple(r.get("provenance", ()))) for r in document.get("relationships", ()))
        self._by_exercise: dict[str, list[Relationship]] = {}
        self._by_family: dict[str, list[str]] = {}
        for row in self._rows:
            self._by_exercise.setdefault(row.source_exercise_id, []).append(row)
            if row.relationship == "member_of_family": self._by_family.setdefault(row.family_id, []).append(row.source_exercise_id)
        for key in self._by_exercise: self._by_exercise[key].sort(key=lambda x: (x.relationship, x.target_exercise_id or ""))
        for key in self._by_family: self._by_family[key] = sorted(set(self._by_family[key]))

    @classmethod
    def load(cls, path: str | Path | None = None, *, db: Any | None = None) -> "RelationshipRegistry":
        path = path or files("fedbpp").joinpath("data", "exercise-relationships.json")
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), db=db)
    @classmethod
    def from_dict(cls, document: dict[str, Any], *, db: Any | None = None) -> "RelationshipRegistry": return cls(document, db=db)
    def family_for(self, exercise_id: str) -> Family | None:
        rows = [r for r in self._by_exercise.get(exercise_id, ()) if r.relationship == "member_of_family"]
        return self._families[rows[0].family_id] if rows else None
    def exercises_in_family(self, family_id: str) -> list[str]:
        if family_id not in self._families: raise KeyError(f"unknown familyId: {family_id}")
        return list(self._by_family.get(family_id, ()))
    members = exercises_in_family
    def related_exercises(self, exercise_id: str, *, same_family: bool = True) -> list[Relationship]:
        family = self.family_for(exercise_id)
        if same_family and family:
            return [self.relationship(exercise_id, target) for target in self.exercises_in_family(family.family_id) if target != exercise_id]
        out = [r for r in self._rows if r.source_exercise_id == exercise_id and r.target_exercise_id]
        out += [Relationship(r.target_exercise_id, r.family_id, r.relationship, r.dimensions, r.confidence, r.source_exercise_id, r.provenance) for r in self._rows if r.target_exercise_id == exercise_id]
        return sorted(out, key=lambda r: (r.target_exercise_id or "", r.relationship))
    def variations(self, exercise_id: str) -> list[Relationship]: return self.related_exercises(exercise_id, same_family=True)
    def variant_dimensions(self, exercise_id: str) -> dict[str, Any]:
        row = next((r for r in self._by_exercise.get(exercise_id, ()) if r.relationship == "member_of_family"), None)
        return dict(row.dimensions) if row else {}
    def same_family(self, exercise_a: str, exercise_b: str) -> bool:
        a, b = self.family_for(exercise_a), self.family_for(exercise_b)
        return bool(a and b and a.family_id == b.family_id)
    def relationship(self, exercise_a: str, exercise_b: str) -> Relationship | None:
        if exercise_a == exercise_b: return None
        explicit = next((r for r in self._rows if r.source_exercise_id == exercise_a and r.target_exercise_id == exercise_b), None)
        if explicit is not None: return explicit
        if not self.same_family(exercise_a, exercise_b): return None
        differences = self.compare_dimensions(exercise_a, exercise_b)["differences"]
        typed = {"equipment":"equipment_variant_of", "grip":"grip_variant_of", "stance":"stance_variant_of", "angle":"angle_variant_of", "laterality":"laterality_variant_of"}
        relation = typed.get(next(iter(differences))) if len(differences) == 1 else None
        left = next(r for r in self._by_exercise[exercise_a] if r.relationship == "member_of_family")
        right = next(r for r in self._by_exercise[exercise_b] if r.relationship == "member_of_family")
        return Relationship(exercise_a, left.family_id, relation or "variation_of", differences, "high" if left.confidence == right.confidence == "high" else "medium", exercise_b, ({"type":"runtime_derivation", "rationale":"Shared curated family; relation derived from inspectable dimensions."},))
    def compare_dimensions(self, exercise_a: str, exercise_b: str) -> dict[str, Any]:
        a, b = self.variant_dimensions(exercise_a), self.variant_dimensions(exercise_b)
        same = self.same_family(exercise_a, exercise_b)
        return {"sameFamily": same, "familyId": self.family_for(exercise_a).family_id if same else None, "differences": {k: [a.get(k), b.get(k)] for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}}
    def related_candidates(self, exercise_id: str, *, equipment: str | None = None, movement_pattern: str | None = None, laterality: str | None = None) -> list[Relationship]:
        candidates = self.related_exercises(exercise_id, same_family=True)
        result=[]
        for relation in candidates:
            target=relation.target_exercise_id; dimensions=self.variant_dimensions(target) if target else {}
            if equipment is not None and dimensions.get("equipment") != equipment: continue
            if laterality is not None and dimensions.get("laterality") != laterality: continue
            if movement_pattern is not None:
                if self.db is None: raise ValueError("movement_pattern filtering requires db")
                if movement_pattern not in self._exercise_data(target)["annotation"].get("patterns", ()): continue
            result.append(relation)
        return result
    def search_families(self, query: str) -> list[Family]:
        needle=query.casefold()
        return sorted((family for family in self._families.values() if needle in family.family_id.casefold() or needle in family.name.casefold() or any(needle in alias.casefold() for alias in family.aliases)), key=lambda x:x.family_id)
    def _exercise_data(self, exercise_id: str, db: Any | None = None) -> dict[str, Any]:
        db=db or self.db
        if db is None: raise ValueError("structural comparison requires db")
        exercise=db.get_exercise(exercise_id) if hasattr(db,"get_exercise") else db["exercises"][exercise_id]
        return exercise.data if hasattr(exercise,"data") else exercise
    def compare_exercises(self, exercise_a: str, exercise_b: str, db: Any | None = None) -> dict[str, Any]:
        left,right=self._exercise_data(exercise_a,db),self._exercise_data(exercise_b,db)
        la,ra=left.get("annotation",{}),right.get("annotation",{})
        def component(key):
            a,b=sorted(set(la.get(key,()))),sorted(set(ra.get(key,())))
            return {"same":a==b,"exerciseA":a,"exerciseB":b}
        equipment_a=left.get("source",{}).get("equipment"); equipment_b=right.get("source",{}).get("equipment")
        return {"exerciseA":exercise_a,"exerciseB":exercise_b,**self.compare_dimensions(exercise_a,exercise_b),"movementPatterns":component("patterns"),"directMuscles":component("direct"),"indirectMuscles":component("indirect"),"stabilizers":component("stabilizers"),"equipment":{"same":equipment_a==equipment_b,"exerciseA":equipment_a,"exerciseB":equipment_b}}
    def compare_exercise_coverage(self, exercise_a: str, exercise_b: str, db: Any | None = None) -> dict[str, Any]:
        db = db or self.db
        if db is None: raise ValueError("compare_exercise_coverage requires db")
        def read(eid):
            ex = db.get_exercise(eid) if hasattr(db, "get_exercise") else db["exercises"][eid]
            ann = ex.annotation if hasattr(ex, "annotation") else ex.get("annotation", {})
            credits = db.metadata.get("setCredits", {"direct":1.0,"indirect":.5,"stabilizer":0.0}) if hasattr(db, "metadata") else db.get("metadata", {}).get("setCredits", {"direct":1.0,"indirect":.5,"stabilizer":0.0})
            roles = {k: sorted(set(ann.get(k, ()))) for k in ("direct", "indirect", "stabilizers")}
            effective = {m: (m in roles["direct"])*credits["direct"] + (m in roles["indirect"])*credits["indirect"] + (m in roles["stabilizers"])*credits["stabilizer"] for m in sorted(set().union(*map(set, roles.values())))}
            return roles | {"effectiveSets": effective}
        a, b = read(exercise_a), read(exercise_b)
        def role_delta(role): return {"added":sorted(set(b[role])-set(a[role])),"removed":sorted(set(a[role])-set(b[role]))}
        return {"exerciseA": exercise_a, "exerciseB": exercise_b, "structural": self.compare_exercises(exercise_a, exercise_b, db), "coverageDifference": {"direct":role_delta("direct"), "indirect":role_delta("indirect"), "stabilizers":role_delta("stabilizers"), "effectiveSetDelta": {m: round(b["effectiveSets"].get(m, 0)-a["effectiveSets"].get(m, 0), 6) for m in sorted(set(a["effectiveSets"]) | set(b["effectiveSets"])) if b["effectiveSets"].get(m, 0) != a["effectiveSets"].get(m, 0)}}}

def family_coverage(plan: dict[str, Any], registry: RelationshipRegistry) -> dict[str, Any]:
    from ._analysis.policies import planned_set_range, representative_scalar
    def add_range(total, value):
        for bound in ("min","target","max"):
            if total[bound] is None or value.get(bound) is None: total[bound]=None
            else: total[bound]=round(total[bound]+float(value[bound]),6)
    result: dict[str, dict[str, Any]] = {}
    for session in plan.get("sessions", []):
        for prescription in session.get("exercises", []):
            eid = prescription.get("exerciseId"); family = registry.family_for(eid) if eid else None
            if not family: continue
            row = result.setdefault(family.family_id, {"familyId": family.family_id, "name": family.name, "exerciseIds": set(), "plannedSetRanges": {"min":0.0,"target":0.0,"max":0.0}, "sessions": set(), "variantDimensions": {}})
            row["exerciseIds"].add(eid); add_range(row["plannedSetRanges"],planned_set_range(prescription)); row["sessions"].add(session.get("planSessionId", session.get("sessionId"))); row["variantDimensions"][eid] = registry.variant_dimensions(eid)
    for row in result.values():
        row["exerciseIds"] = sorted(row["exerciseIds"]); row["sessions"] = sorted(x for x in row["sessions"] if x is not None); row["sessionExposures"] = len(row["sessions"])
        row["plannedSets"] = representative_scalar(row["plannedSetRanges"])
        used={}
        for dimensions in row["variantDimensions"].values():
            for key,value in dimensions.items(): used.setdefault(key,set()).add(value)
        row["variantDimensionsUsed"]={key:sorted(values) for key,values in sorted(used.items())}
    return {k: result[k] for k in sorted(result)}

__all__ = ["Family", "Relationship", "RelationshipRegistry", "family_coverage"]
