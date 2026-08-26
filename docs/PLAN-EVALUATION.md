# PlanEvaluation

```python
from fedbpp import evaluate_plan
result = evaluate_plan(plan, db, profile=profile, target=target,
                       relationships=relationships)
```

The evaluator reuses canonical PLAN coverage, including authoritative
`metadata.setCredits`, range preservation, `volumeEligible`, native-cycle
frequency, and seven-day normalization. It returns muscle coverage, frequency,
movement patterns, optional family context, equipment compatibility,
availability, preferences, hard constraints, completeness, warnings, and
provenance.

`valid`, `valid_with_target_gaps`, `hard_constraint_violation`, and
`incomplete_coverage` describe the result. A target gap is distinct from a
profile violation, and soft preferences never become failures. Unknown DB
exercise IDs and unknown equipment remain visible as incomplete evaluation.

When `profile.availability.exercisesPerSession` is present, `exerciseCounts`
contains one deterministic entry per session with `exerciseCount`, `minimum`,
`target`, `maximum`, and `state`. Below-minimum and above-maximum are hard
constraint violations. A target miss inside the hard range is a soft
preference finding only.

Duration estimation is intentionally deferred; no exact minutes are invented.
Plan generation, recommendations, progression, and adaptive coaching are not
part of v1.6.
