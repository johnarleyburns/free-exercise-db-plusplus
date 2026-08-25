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
Credits are authoritatively read from the analyzed database’s
`metadata.setCredits`; normal analysis fails clearly if any direct, indirect, or
stabilizer credit is missing, invalid, non-finite, or negative. The shipped
database currently declares direct `1.0`, indirect `0.5`, and stabilizer `0.0`.
The low-level `set_credits(..., allow_legacy_defaults=True)` option is the only
explicit compatibility path for legacy synthetic databases.

## Units and counting

`src.analysis.units` only converts known compatible units. Unknown units and
dimension changes raise `UnitError`; analysis never guesses that a value is
kilograms, metres, or seconds. `src.analysis.policies` contains reusable
planned-set and completed-set counting policies so callers can choose and
record policy explicitly.

RPE/RIR and compatible volume-load adherence are reported separately; they never weight the DB++ effective-set model. Estimated-1RM remains out of scope.

## Hardened volume semantics

All results name `dbpp-default-volume-v1` and read direct, indirect, and stabilizer credits from the analyzed database's `metadata.setCredits`. Completed warmup, technique, test, isometric, and other sets are excluded; working, backoff, AMRAP, drop, cluster, rest-pause, and assisted parent sets count once. Macro-segments and unilateral labels never multiply a parent observation.

`volumeEligible=false` prescriptions remain mapped and appear in completeness diagnostics, but contribute no resistance-volume muscle, stabilizer, effective-set, or movement-pattern totals. Coverage preserves `min`/`target`/`max` ranges under the `*SetRanges` keys. Unspecified bounds remain null: minimum-only, target-only, maximum-only, and min/max prescriptions are not converted to exact values. Scalar convenience views use the explicit target, then minimum, then maximum representative policy only where a scalar is required.

PLAN-vs-PLAN frequency includes deterministic session, exercise-prescription,
exercise, muscle-exposure, and movement-pattern-exposure comparisons. Muscle and
pattern exposures report both native-cycle and normalized seven-day values.
Muscle-level research CSV rows retain separate planned min, target, and max
columns for direct, indirect, stabilizer, and effective sets; absent bounds stay
empty.

Phase-specific cycle lengths are normalized independently. Cross-phase normalized averages are weighted by `durationCycles`. Provenance records analysis/policy versions, database provenance, document schema versions, credits, periods, range policy, and unit policy.

Load, RPE, RIR, and volume-load adherence remain separate from effective sets. Only known compatible mass units are compared; RPE and RIR are never inferred from each other.
