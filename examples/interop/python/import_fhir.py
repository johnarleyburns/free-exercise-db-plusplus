import json
from fedbpp import import_workout

with open("fhir-input.json", encoding="utf-8") as handle:
    result = import_workout("fhir", json.load(handle))
print(json.dumps(result.document, indent=2, sort_keys=True))
print(json.dumps(result.report(), indent=2, sort_keys=True))
