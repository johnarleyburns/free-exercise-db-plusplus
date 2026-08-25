# v1.3 import/export

v1.3 adds deterministic conversion on top of the v1.2 mapping registry. The
canonical pipeline is external document → adapter model → mapping registry →
DB++ ACTUAL → schema validation, with the reverse pipeline for export.

## Support matrix

| Format | Import | Export | Identity mapping | Loss report | Notes |
|---|---:|---:|---|---:|---|
| FHIR R4 Bundle | yes | yes | reviewed exact DB++ coding subset | yes | FHIR Physical Activity IG 1.0.0 STU1; strength detail uses documented extensions/projections |
| Garmin FIT | planned/optional | planned/optional | reviewed v1.2 crosswalk retained | n/a | no FIT SDK is vendored; binary support is not claimed |
| Health Connect | projection model | projection model | category only | yes | API ecosystem, not a portable file format |
| HealthKit | projection model | projection model | no standard exercise identity | yes | API ecosystem, not a portable file format |

FHIR input is a `Bundle` of `Observation` resources. Exercise identity is read
only from the reviewed DB++ FHIR coding registry; names are never fuzzy matched.
FHIR exports use deterministic resource IDs (`set-EEEE-SSSS`) and canonical JSON
ordering when emitted by the CLI.

Programmatic conversion is strict by default:

```python
from fedbpp import import_workout, export_workout

actual = import_workout("fhir", document, mode="strict")
external = export_workout("fhir", actual.document, mode="allow-lossy")
print(external.status, external.report())
```

`lossless` means no conversion loss; `normalized` records representational
normalization such as pounds to kilograms; `lossy` means a meaningful field was
not represented; `unsupported` and `invalid` describe failed inputs/policies.
`allow-lossy` permits known loss only when every loss is included in the result
and optional report. It never permits malformed input or ambiguous identity.

Unknown exercises survive import with `exerciseName` and `externalExerciseId`.
They receive no DB++ anatomy. Ambiguous and broad/category mappings are never
selected as exact identities.

The FHIR coding extension preserves the DB++ exercise identifier, schema/version,
mapping version, and adapter version where the target representation permits it.
FHIR is intended here as a physical-activity interchange boundary, not a claim
of complete clinical interoperability.
