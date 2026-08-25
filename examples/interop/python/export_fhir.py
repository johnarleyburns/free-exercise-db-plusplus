import json
from fedbpp import export_workout

with open("actual.json", encoding="utf-8") as handle:
    result = export_workout("fhir", json.load(handle), mode="allow-lossy")
print(json.dumps(result.document, indent=2, sort_keys=True))
print(json.dumps(result.report(), indent=2, sort_keys=True))
