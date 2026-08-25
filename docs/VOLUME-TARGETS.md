# Volume TARGET 0.1

`volume-target.schema.json` defines small, explicit criteria for planned muscle volume.
Targets are separate from both Workout PLAN prescriptions and derived analysis output.
A target profile identifies a native `periodDays`; it never silently assumes a calendar week.

Each muscle may provide `min`, `target`, `max`, or any combination. The analysis
comparison uses DB++ effective sets as its default metric and reports:

- `below_minimum` when actual volume is below `min`;
- `above_maximum` when actual volume exceeds `max`;
- `within_range` otherwise.

A target-only value is retained as the desired reference while the current 0.1 gap
classification remains `within_range` unless a minimum or maximum bound is supplied.
Future versions may add explicit target tolerances and movement-pattern targets.

## Analysis APIs

```python
from src.analysis import analyze_plan, compare_to_targets

coverage = analyze_plan(plan, database)
gaps = compare_to_targets(plan, target_profile, database)
```

`analyze_plan` reports direct, indirect, stabilizer participation, effective sets,
and movement-pattern sets separately. It retains native-cycle totals and includes an
explicit seven-day normalized view. Ranged PLAN set counts use target, then minimum,
then maximum, and this policy is recorded in `analysisMetadata`.

Custom or unknown exercises remain in the plan but contribute to `unmappedSets` and
never receive inferred muscle or pattern roles. Known volume-ineligible exercises are
reported separately as `ineligibleSets`.

The reference implementation uses DB++ credits exactly: direct `1.0`, indirect `0.5`,
and stabilizer `0.0`. These are analytical accounting conventions, not physiological
equivalence claims.

## Comparison states

The deterministic states are `below_minimum`, `within_range_below_target`, `at_target`, `within_range_above_target`, `above_maximum`, and `not_targeted`. Profiles without a target midpoint use `within_range`; no midpoint is invented. Results include the PLAN effective-set range, the target bounds, target delta, and period. `validate_target(target, db=db)` optionally rejects muscle IDs absent from the DB++ ontology while schema-only validation remains available.
