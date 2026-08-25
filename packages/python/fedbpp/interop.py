from dataclasses import dataclass
import json
from pathlib import Path
from importlib.resources import files
@dataclass(frozen=True)
class MappingMatch:
    system:str; external_id:str; dbpp_exercise_id:str|None; external_name:str; relation:str; direction:str; confidence:str; provenance:dict
class MappingRegistry:
    def __init__(self,records): self._records=tuple(sorted(records,key=lambda x:(x.system,x.external_id,x.dbpp_exercise_id or "",x.relation)))
    @classmethod
    def load(cls,path=None):
        if path is None: path=files("fedbpp").joinpath("interop_data")
        p=Path(path); fs=sorted(p.glob("*.json")) if p.is_dir() else [p]; out=[]
        for f in fs:
            d=json.loads(f.read_text())
            for e in d.get("entries",[]):
                for x in (e.get("dbppExerciseIds") or [None]): out.append(MappingMatch(d["target"],e["externalId"],x,e["externalName"],e["relation"],e["direction"],e["confidence"],e["provenance"]))
        return cls(out)
    def lookup_external(self,system,external_id): return [x for x in self._records if x.system==system and x.external_id==external_id]
    def lookup_dbpp(self,exercise_id,system=None): return [x for x in self._records if x.dbpp_exercise_id==exercise_id and (system is None or x.system==system)]
