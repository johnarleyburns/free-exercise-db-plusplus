# PLAN-vs-PLAN comparison

`compare_plans(plan_a, plan_b, db)` compares two immutable PLAN revisions without
linking either document to ACTUAL observations. It reports direct, indirect,
stabilizer participation, effective sets, movement-pattern sets, and session/exercise
frequencies.

Both native-cycle totals and explicit seven-day normalized totals are included. The
metadata retains each plan’s native cycle length; normalization never overwrites the
source prescription. DB++ credits remain direct `1.0`, indirect `0.5`, and stabilizer
`0.0`.

```python
from src.analysis import compare_plans, write_json, write_tidy_csv

comparison = compare_plans(plan_a, plan_b, database)
write_json(comparison, "plan-comparison.json")
write_tidy_csv(comparison, "plan-comparison.csv")
```

The CSV is deterministic tidy output with `kind`, `period`, `metric`, `key`, `planA`,
`planB`, and `delta` columns. JSON keys and CSV rows are sorted for reproducible
research and review workflows. PLAN-vs-ACTUAL matching is intentionally deferred to a
later roadmap sprint.
