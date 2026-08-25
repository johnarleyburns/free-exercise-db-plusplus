# ADR 0015: Plan assignment artifact

Status: accepted (v1.6)

No `plan-assignment.schema.json` is added. PLAN `planId`/`revisionId` and the
existing TrainingHistory activation model are sufficient for portable plan
identity and longitudinal linkage. Trainer applications may store assignment,
permissions, messaging, and application metadata externally.
