# PLAN-vs-PLAN comparison

`compare_plans(plan_a, plan_b, db)` compares two immutable PLAN revisions without
linking either document to ACTUAL observations. It reports direct, indirect,
stabilizer participation, effective sets, movement-pattern sets, and session/exercise
frequencies. Muscle and movement-pattern exposure comparisons include native-cycle
counts and normalized exposures per seven days.

Both native-cycle totals and explicit seven-day normalized totals are included. The
metadata retains each plan’s native cycle length; normalization never overwrites the
source prescription. Credits come from authoritative `metadata.setCredits`; malformed
or incomplete credit metadata causes analysis to fail.

```python
from src.analysis import compare_plans, write_json, write_tidy_csv

comparison = compare_plans(plan_a, plan_b, database)
write_json(comparison, "plan-comparison.json")
write_tidy_csv(comparison, "plan-comparison.csv")
```

The CSV is deterministic tidy output with `kind`, `period`, `metric`, `key`, `planA`,
`planB`, and `delta` columns. JSON keys and CSV rows are sorted for reproducible
research and review workflows. PLAN-vs-ACTUAL matching is documented separately in `PLAN-ACTUAL.md`.

## Ranges and provenance

Comparisons preserve min/target/max deltas in `nativeCycle.ranges` and
`normalized7Day.ranges`; absent bounds remain null and their deltas remain null.
Existing scalar comparisons use target, then min, then max only when a representative
value is required. Metadata identifies both PLAN schema versions, complete DB
provenance and policies, authoritative set credits, and both native periods.
Periodized coverage honors phase-specific cycles and duration weighting before
comparison.
