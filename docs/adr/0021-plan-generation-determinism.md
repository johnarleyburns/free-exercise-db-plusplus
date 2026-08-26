# ADR 0021: Deterministic PLAN generation

Status: accepted (v1.8)

PLAN generation produces a proposal from a TrainingProfile, TARGET, DB++, an
explicit PlanningPolicy, and optional state, relationships, and current PLAN.
It is deterministic: there are no random choices, clocks, UUIDs, remote
services, LLMs, or hidden ordering dependencies in plan content.

The generator does not claim physiological optimality. A policy documents its
construction choices, including split, allocation, rep range, and tie-breaks.
`evaluate_plan()` is the canonical acceptance and quality gate; a successful
proposal contains that evaluator result unchanged and has first passed PLAN
schema validation.

The priority order is: (1) valid PLAN, (2) hard TrainingProfile and request
constraints, (3) TARGET minimums, (4) TARGET values, (5) soft preferences,
and (6) deterministic tie-breaking. Hard conflicts yield `unsatisfiable`.
Hard-valid drafts that cannot reach a TARGET minimum yield
`generated_with_target_gaps`.

Generation neither assigns nor activates a PLAN, observes history
continuously, applies CoachDecision, nor revises an active plan. A generated
PLAN is a draft for either trainer or self-trained workflows.
