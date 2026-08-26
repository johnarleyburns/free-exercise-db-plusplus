# TrainingState

`derive_training_state(history, db, as_of=..., window=...)` returns a deterministic,
derived summary of recent ACTUAL observations and the active PLAN context.
`as_of` is required. Windows are inclusive by local calendar date: `last_7_days`
and `last_28_days`, `current_plan_cycle`, `current_phase`, or a custom
`{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}` range. Future workouts are
excluded. Explicit timestamp offsets are honored and naive timestamps require a
timezone.

The state exposes exercise observations, optional family context, canonical
muscle rows from longitudinal analysis, adherence/session rows, and provenance.
It preserves missingness rather than turning absent work into zero. ACTUAL is
the underlying truth; state is not manually edited and does not mutate PLAN.
