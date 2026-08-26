# TrainingProfile

TrainingProfile is the portable description of a subject’s training context.
It contains no required name, contact information, date of birth, diagnosis,
or medical record number. `subjectId`, when present, is opaque.

The initial goal vocabulary is `hypertrophy`, `strength`,
`muscular_endurance`, `general_fitness`, `skill_practice`, and `power`.
`experience` is `novice`, `intermediate`, `advanced`, or `unknown`. Neither
field changes v1.6 evaluation behavior.

Availability uses optional partial ranges. `sessionsPerCycle.min` and `.max`
are hard bounds; `.target` is contextual. `cycleLengthDays` and day offsets
avoid calendar assumptions. Equipment values follow DB++ source equipment
values, including `body only`; `bodyweight`, `no equipment`, and `none` are
accepted aliases for availability validation.

`availability.exercisesPerSession` follows the same partial-range shape. Its
minimum and maximum are hard construction/evaluation bounds; its target is a
soft preference. This field was added in v1.10 and is also the canonical
destination for a resolved WorkoutIntent session constraint.

Preferences are soft: preferred and avoided exercises/families produce
findings. Constraints are hard: excluded exercise/family IDs produce failures.
Contradictory preference/exclusion entries are validation errors.
