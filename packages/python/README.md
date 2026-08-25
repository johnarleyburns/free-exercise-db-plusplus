# fedbpp Python package

Standalone helpers for DB++, Workout ACTUAL, Workout PLAN 0.1/0.2, Volume TARGET, and derived analysis. Install from this directory with `pip install .` or use `pip install -e .` during development. Built wheels include their schemas and reference analysis implementation; they never import repository-level `src.*`. JSON Schema validation uses the optional `jsonschema` dependency.

```python
from fedbpp import (Database, Workout, Plan, VolumeTarget, analyze_plan,
                    compare_plans, compare_to_targets, compare_plan_actual)

db = Database.load("free-exercise-db-plusplus.json")
workout = Workout.load("examples/workout.example.json")
print(workout.effective_sets(db))
plan = Plan.load("examples/plans/periodized-0.2.json")
print(analyze_plan(plan, db)["nativeCycle"])
bench = db.get_exercise("Barbell_Bench_Press_-_Medium_Grip")
```

The helper never mutates source documents and does not infer energy, body mass, or muscle credits beyond DB++ direct/indirect/stabilizer semantics.


The installed wheel is standalone. Its PLAN analysis follows
`dbpp-default-volume-v1`, requires complete finite non-negative direct, indirect,
and stabilizer credits in database metadata, preserves absent range bounds, excludes
volume-ineligible exercises from resistance-volume totals, and exposes conservative
PLAN/ACTUAL load and effort comparisons. Scalar views use target, then min, then max
only when a representative is required. Advanced adherence is currently a Python
reference capability; Swift, Kotlin, and R documentation only claims the functions
each package implements.
