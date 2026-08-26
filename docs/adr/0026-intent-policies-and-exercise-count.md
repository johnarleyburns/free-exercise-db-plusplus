# ADR 0026: intent policies and exercise count

Status: accepted (v1.10)

Goal and environment policies are independently versioned artifacts. An
environment is only an intent convenience label: it always resolves to
concrete DB++ equipment before the generator sees the profile. `custom` has
no hidden preset and therefore needs explicit equipment.

Per-session exercise count is normalized into TrainingProfile availability.
`min` and `max` are hard constraints in both `evaluate_plan()` and
`generate_plan()`; `target` is a soft preference. A plan that cannot meet
coverage while respecting the maximum is hard-valid with
`generated_with_target_gaps`, or `unsatisfiable` if it cannot construct a
schema-valid plan satisfying hard bounds. No count is fabricated for a partial
range.
