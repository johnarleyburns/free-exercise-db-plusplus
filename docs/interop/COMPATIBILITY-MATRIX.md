# Compatibility matrix

This is a capability matrix, not a claim of physiological equivalence. `conversion` means units or representation change; `extension` means target-specific data is needed.

| Concept | FIT | Health Connect | HealthKit | FHIR PA | IEEE/Open mHealth | Google Fit legacy |
|---|---|---|---|---|---|---|
| exercise identity/name/custom | extension/lossy | extension/lossy | extension/lossy | coding/extension | extension | lossy |
| DB++ exerciseId/equipment/laterality | extension | extension | extension | extension | extension | unsupported |
| ACTUAL session timestamps/time zones | conversion | lossless/conversion | lossless | conversion | conversion | conversion |
| occurrence/set order/reps/load | conversion/lossy | extension/unknown | extension | extension | extension | conversion/lossy |
| duration/distance/rest | conversion | conversion | conversion | conversion | conversion | conversion |
| RPE/RIR/tempo/set type/completion | extension/lossy | extension/unsupported | metadata/extension | extension | extension | lossy |
| segments/rep telemetry/provenance | extension | segments + metadata | events + samples | Provenance/extension | extension | lossy |
| PLAN/prescriptions/ranges/phases/progression | Workout steps, limited | planned feature, limited | unsupported/extension | extension | unknown | unsupported |
| TARGET | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
