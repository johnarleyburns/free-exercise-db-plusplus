# ADR 0014: Deterministic PlanEvaluation

Status: accepted (v1.6)

PlanEvaluation calls the existing canonical PLAN coverage analysis and target
comparison. It keeps target gaps, hard constraint violations, soft preference
findings, and completeness separate. It emits no opaque quality score and does
not mutate PLAN. Frequency is session exposure normalized from the PLAN native
cycle to seven days. Relationship data is optional; muscle and movement
analysis remains available without it.
