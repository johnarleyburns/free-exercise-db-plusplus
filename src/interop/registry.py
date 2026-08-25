from dataclasses import dataclass
import json
from pathlib import Path

@dataclass(frozen=True)
class MappingMatch:
    system: str
    external_id: str
    dbpp_exercise_id: str | None
    external_name: str
    relation: str
    direction: str
    confidence: str
    provenance: dict
    mapping_kind: str = "identity"

    @property
    def is_identity(self): return self.relation == "exact"

    @property
    def is_category(self): return self.mapping_kind == "category"

    @property
    def is_ambiguous(self): return self.is_category or self.relation in {"broader", "approximate"}

class MappingRegistry:
    def __init__(self, records):
        self._records=tuple(sorted(records,key=lambda x:(x.system,x.external_id,x.dbpp_exercise_id or "",x.relation,x.direction)))
    @classmethod
    def load(cls,path=None):
        p=Path(path) if path is not None else Path(__file__).parents[2]/"mappings"
        fs=sorted(p.glob("*.json")) if p.is_dir() else [p]; out=[]
        for f in fs:
            d=json.loads(f.read_text())
            if d.get("mappingKind") not in {"identity", "category"}: continue
            for e in d.get("entries",[]):
                if d["mappingKind"] == "category":
                    out.append(MappingMatch(d["target"],e["sourcePath"],None,e["sourcePath"],"category",e.get("direction","external_to_dbpp"),"high",{"source":d["targetSpecification"]["references"][0],"rationale":e["notes"]},d["mappingKind"]))
                else:
                    for x in (e.get("dbppExerciseIds") or [None]):
                        out.append(MappingMatch(d["target"],e["externalId"],x,e["externalName"],e["relation"],e["direction"],e["confidence"],e["provenance"],d["mappingKind"]))
        return cls(out)
    def lookup_external(self,system,external_id): return [x for x in self._records if x.system==system and x.external_id==external_id]
    def lookup_dbpp(self,exercise_id,system=None): return [x for x in self._records if x.dbpp_exercise_id==exercise_id and (system is None or x.system==system)]
    def exact_matches(self,system,external_id): return [x for x in self.lookup_external(system,external_id) if x.relation=="exact"]
    def is_ambiguous(self,system,external_id):
        matches=self.lookup_external(system,external_id)
        return len(matches) > 1 or any(match.is_ambiguous for match in matches)
