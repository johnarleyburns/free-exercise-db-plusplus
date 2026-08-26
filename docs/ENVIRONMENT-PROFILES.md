# Environment profiles

Environment labels resolve to explicit DB++ equipment vocabulary before
planning. `commercial-gym-general-v1` contains `bands`, `barbell`, `body
only`, `cable`, `dumbbell`, `e-z curl bar`, `exercise ball`, `kettlebells`,
`machine`, and `medicine ball`. It is a common-gym convenience preset, not a
guarantee that every commercial gym has every item.

`bodyweight-only-v1` resolves exactly to `body only`; the conservative
`minimal-equipment-general-v1` resolves to `bands`, `body only`, and
`dumbbell`. These are policy-owned exact sets: changing one requires a new
policy version. Intent `addEquipment`/`removeEquipment` apply after the
preset. Explicit existing TrainingProfile equipment remains authoritative,
then those explicit intent overrides apply. `custom` applies no preset and
requires explicit normalized DB++ equipment; labels such as “bench” or
“pullup bar” are not invented when they are absent from the DB++ equipment
vocabulary.
