# DB++ interoperability audit

Review date: 2026-08-25. This document records capability, not an exporter. v1.2 maps stable DB++ concepts to the reviewed target and reports loss explicitly; v1.3 may add operational adapters.

Capability labels: `lossless`, `representable_with_conversion`, `representable_with_extension`, `lossy`, `unsupported`, `not_applicable`, `unknown`. A notes/metadata string is not treated as lossless support.

## HL7 US Physical Activity Implementation Guide

Specification/API: US Physical Activity IG 1.0.0 STU1 on FHIR R4, reviewed 2026-08-25.

The IG is a physical-activity assessment/recording model, not a resistance set interchange contract. Activity timing, coding, quantity and provenance can be represented with conversion; DB++ sets, prescriptions, RIR/RPE and exercise variants are generally extension/unsupported.

Authoritative reference: [https://hl7.org/fhir/us/physical-activity/STU1/](https://hl7.org/fhir/us/physical-activity/STU1/)

| DB++ concept | Assessment |
|---|---|
| identity/name/custom exercise | lossy or extension_required |
| timestamps/time zones/provenance | representable_with_conversion |
| ACTUAL occurrence, reps, load, duration, distance | representable_with_conversion where target fields exist |
| RPE/RIR/tempo/set type/laterality/substitution | extension_required, lossy, or unsupported |
| PLAN, arbitrary cycles, progression, TARGET | unsupported or target-specific extension |
