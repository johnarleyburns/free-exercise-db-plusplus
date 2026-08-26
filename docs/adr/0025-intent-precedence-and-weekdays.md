# ADR 0025: intent precedence and weekdays

Status: accepted (v1.10)

Precedence is: (1) hard explicit WorkoutIntent constraints, (2) explicit
TARGET fields, (3) explicit TrainingProfile hard constraints, (4) explicit
WorkoutIntent soft preferences, (5) profile preferences, (6) goal-policy
defaults, and (7) environment-policy defaults. This is a precedence model,
not permission for a lower-priority value to defeat a hard constraint:
contradictory hard inputs return `invalid` with machine-readable conflicts.
Explicit TARGET values merge field-by-field over goal defaults and preserve
partial ranges.

Explicit profile equipment is authoritative over an environment shortcut.
Intent equipment additions/removals are explicit overrides and are applied to
that authoritative set. Without profile equipment, the environment policy
resolves to a normalized DB++ equipment set before generation.

Weekdays are normative only for `cycleLengthDays: 7`: Monday=0, Tuesday=1,
Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6. Weekday fields on
another cycle length are invalid; no modulo/calendar mapping is guessed.
