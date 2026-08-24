# fedbpp Python package

Dependency-light helpers for loading the DB++ database and Workout interchange JSON. Install from this directory with `pip install -e .` when a project packaging configuration is added, or add `packages/python` to `PYTHONPATH` during development. JSON Schema validation uses the optional `jsonschema` dependency.

```python
from fedbpp import Database, Workout

db = Database.load("free-exercise-db-plusplus.json")
workout = Workout.load("examples/workout.example.json")
print(workout.effective_sets(db))
bench = db.get_exercise("Barbell_Bench_Press_-_Medium_Grip")
```

The helper never mutates source documents and does not infer energy, body mass, or muscle credits beyond DB++ direct/indirect/stabilizer semantics.
