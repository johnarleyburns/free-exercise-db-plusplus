# ADR 0024: WorkoutIntent boundary

Status: accepted (v1.10)

WorkoutIntent represents the current, structured planning request. It may state
a goal, schedule, exercise-count constraint, environment shortcut, continuity
preference, or request to use supplied history. It is deliberately not natural
language and contains no required PII.

TrainingProfile remains persistent subject/environment context: available
equipment, exclusions, preferences, experience, and availability. TARGET
remains desired coverage: muscle effective sets, frequency, movement-pattern,
and family ranges. A WorkoutIntent neither replaces nor becomes either of
those artifacts. Policies are the separately-versioned rules that resolve a
high-level goal/environment into defaults.

Resolution is explicit, pure, deterministic, and provenance-backed. It does
not generate a PLAN. It cannot silently override a persistent hard profile
exclusion; conflicts are returned as machine-readable result entries.
