# PLAN generation

```python
from fedbpp import generate_plan

result = generate_plan(profile, target, db,
                       policy="full-body-general-v1",
                       training_state=state,
                       relationships=relationships)
```

`result` is a structured draft: `status`, canonical `plan`, unchanged canonical
`evaluation`, `policy`, per-exercise `selectionRationale`, unsatisfied hard
constraints, minimum-target gaps, soft-preference findings, and provenance.
The statuses are `generated` (hard constraints and target minima met),
`generated_with_target_gaps` (hard-valid but one or more minima cannot be
met), `unsatisfiable` (a hard constraint or valid PLAN construction cannot be
satisfied), and `invalid_input`.

Candidate exercises are explicitly sorted by exerciseId and filtered before
ranking: they must be `volumeEligible`, have verifiable available equipment,
and not be excluded by exercise or family. Unknown/`other` equipment is
rejected by the shipped policy. Family data is optional except where a family
constraint or target is requested. Family membership is not equivalence.

The allocator repeatedly evaluates the candidate PLAN with `evaluate_plan()`.
It works on the greatest remaining minimum deficit first, then moves toward
target values, using authoritative `metadata.setCredits` for direct, indirect,
and stabilizer contributions. It does not deliberately exceed a configured
maximum. Frequency requirements select a session without that muscle exposure
before adding repeated exposure. Movement patterns and family targets use the
same evaluator sections.

Hard required and locked exercise IDs must appear; conflicts with exclusions,
unknown IDs, or equipment are reported rather than overridden. Existing PLAN
exercises and successful in-window TrainingState exercise usage are continuity
preferences only. Preferences never defeat hard constraints or target minima.
The response includes a descriptive PLAN difference when `current_plan` is
supplied; the input is never mutated.

Generated IDs are deterministic by default: `generated-plan`, `r1`,
`session-1`, and ordered `rx-SS-NN`. Callers can supply `options.planId` and
`options.revisionId` when they need application-level uniqueness.

Duration is intentionally not made up by generation. The v1.6 duration policy
is deferred because PLAN lacks required rest and transition inputs; the same
limitation is preserved here.

Use the CLI to write clean PLAN JSON separately from the report:

```bash
fedbpp generate-plan --profile profile.json --target target.json --db free-exercise-db-plusplus.json \
  --policy full-body-general-v1 --output generated-plan.json --report generation-report.json
```
