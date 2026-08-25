# ADR 0013: Profile constraint semantics

Status: accepted (v1.6)

`excludedExerciseIds` and `excludedFamilyIds` are hard constraints and produce
machine-readable violations. Preferred and avoided exercise/family IDs are
soft findings only; they never fail a plan and have no preference score.

Availability `min` and `max` for sessions are hard bounds; `target` is
informational. Partial ranges remain partial. Equipment is the available
capability vocabulary from DB++ source metadata; `body only` represents
bodyweight/no-equipment work. Unknown equipment is incomplete verification,
not an automatic failure.
