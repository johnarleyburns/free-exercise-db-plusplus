# Adaptive coaching

`adapt_plan()` is a deterministic, advisory boundary:

```text
ACTUAL/history -> TrainingState -> CoachDecision -> proposed PLAN revision -> evaluate_plan()
```

It is not a mechanism for silently modifying an active PLAN. DB++ never
assigns, activates, sends, persists, or accepts a proposal; applications and
trainers retain those responsibilities. ACTUAL/history and the caller's PLAN
are read-only inputs. A changed proposal receives a deterministic next revision
identity (`r1` becomes `r2`; other IDs receive `-adaptive-1`), while unchanged
prescription and session IDs are retained.

`general-adaptive-v1` uses the canonical 28-day TrainingState window by
default, requires two recent performances before load progression, and requires
two repeated below-minimum performances before conservative load regression.
It is intentionally hold-biased. Progression delegates to v1.7
`double-progression-v1`; RPE/RIR are never converted and retain its corrected
direction semantics. Volume adjustments use DB metadata `setCredits`, are
capped at two total one-set edits, and pass canonical validation/evaluation.

Hard profile constraints outrank every other decision. A current PLAN made
invalid by equipment, exclusions, or availability is regenerated through the
v1.8 generator and returned only as `regeneration_proposed`. Every successful
proposal validates as PLAN and has an unchanged canonical `evaluate_plan()`
result attached. No opaque quality score or physiological-optimality claim is
made.

The result contains `status`, current/proposed PLAN and evaluations,
TrainingState, controlled decisions/reasons, machine-readable changes,
unresolved issues, policy, and reproducibility provenance. Repeating identical
input returns identical output; a `no_change` result never creates a revision.

```python
from fedbpp.coaching import adapt_plan

result = adapt_plan(profile, target, current_plan, history, db,
                    options={"asOf": "2026-08-25T12:00:00Z", "timezone": "UTC"})
```
