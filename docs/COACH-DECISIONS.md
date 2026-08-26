# CoachDecision

CoachDecision is the portable v1.7 advisory result (`coach-decision.schema.json`).
It contains decision type, policy identity, plan/prescription identity,
before/after values, stable reason codes, exact set observations, and
provenance. It never edits or creates a PLAN. Use `suggest_progression(plan,
state, policy=...)` for one decision per PLAN prescription.

The initial reason vocabulary includes `POLICY_HOLD`, rep/set target outcomes,
effort outcomes, missing effort/load, incompatible units, incomplete workout,
missing match/recency, and inactive-plan context.
