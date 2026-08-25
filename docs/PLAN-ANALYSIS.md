# PLAN analysis

PLAN analysis is a derived, read-only view over a PLAN, the stable DB++
exercise database, optional TARGET criteria, and optional ACTUAL observations.
The source JSON documents are never mutated.

## Reference APIs

The low-level reference functions live under `src.analysis`:

```python
from src.analysis import analyze_plan, compare_plans, compare_to_targets

coverage = analyze_plan(plan, db)
revision_delta = compare_plans(plan_a, plan_b, db)
gaps = compare_to_targets(plan, target, db)
```

The Python consumer exposes the same operations through `fedbpp.analysis`:

```python
from fedbpp import analyze_plan, compare_plan_actual, compare_plans, compare_to_targets

coverage = analyze_plan(plan, db)
adherence = compare_plan_actual(plan, actual, db)
delta = compare_plans(plan_a, plan_b, db)
gaps = compare_to_targets(plan, target, db)
```

Coverage keeps direct, indirect, stabilizer participation, effective-set, and
movement-pattern totals separate. Native cycle totals are retained alongside
the explicitly labelled seven-day normalized view. Custom or unknown exercises
remain visible but do not receive inferred muscle roles.

Every analysis result identifies its DB/schema versions and set-credit policy.
The default DB++ credits are direct `1.0`, indirect `0.5`, and stabilizer
`0.0`. Ranged prescriptions use the target value, then minimum, then maximum
as the documented count policy.

## Units and counting

`src.analysis.units` only converts known compatible units. Unknown units and
dimension changes raise `UnitError`; analysis never guesses that a value is
kilograms, metres, or seconds. `src.analysis.policies` contains reusable
planned-set and completed-set counting policies so callers can choose and
record policy explicitly.

RPE/RIR, tonnage, and estimated-1RM calculations remain separate future
analysis models; raw observations are preserved and are not silently weighted
into the DB++ effective-set model.
