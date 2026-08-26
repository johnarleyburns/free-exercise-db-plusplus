# ADR 0022: PlanningPolicy semantics

Status: accepted (v1.8)

PlanningPolicy is a versioned code-defined model rather than an implicit set of
generator constants. It exposes an ID, version, description, split, exercise
selection, volume allocation, frequency, tie-breaking strategies, and named
parameters. No portable JSON policy schema is added: v1.8 does not yet need
user-defined policy interchange.

Reference policies are construction rules, not universal programming advice.
Their parameter choices and ranking order are part of their published
semantics.
