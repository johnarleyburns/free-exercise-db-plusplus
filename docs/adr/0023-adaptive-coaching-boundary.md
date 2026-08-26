# ADR 0023: Adaptive coaching boundary

Status: accepted (v1.9)

Adaptive coaching consumes ACTUAL/history through TrainingState, emits
deterministic CoachDecision records, constructs a proposed PLAN revision, and
uses canonical PLAN validation plus `evaluate_plan()` as its gate. It never
silently changes the current PLAN.

Recommendations are advisory. Proposals are immutable copies with a new,
deterministic revision identity; prior PLAN revisions and ACTUAL records remain
unchanged. Hard constraints always win, no successful proposal knowingly
violates one, and there is no hidden randomness, clock, activation, medical
inference, or physiological-optimality claim.
