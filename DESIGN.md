# Free Exercise DB++ Design Specification

**Specification version:** 0.1.0  
**Status:** Draft  
**Upstream dataset:** yuhonas/free-exercise-db

## Purpose

Free Exercise DB++ (FEDB++) augments Free Exercise DB with a reproducible muscle-volume annotation designed for strength and hypertrophy tracking.

Free Exercise DB's `primaryMuscles` and `secondaryMuscles` describe exercise involvement. They are useful input evidence, but they are not defined as direct-set and indirect-set equivalents. FEDB++ therefore preserves those fields and adds a separate annotation layer.

## Core role model

Each muscle may be assigned one of three mutually exclusive roles for an exercise.

### Direct

A prime mover intentionally loaded through a meaningful contractile range and expected to receive a substantial resistance-training stimulus.

Default set credit: **1.0**

### Indirect

A substantial synergist contributing materially to the movement, but not one of the exercise's principal target/limiting prime movers.

Default set credit: **0.5**

### Stabilizer

Meaningfully active primarily through isometric/supporting action, posture, grip, or joint stabilization.

Default set credit: **0.0**

The numerical credits are bookkeeping defaults, not claims of universal biological equivalence.

## Volume eligibility

Resistance-set accounting defaults:

- strength: eligible
- powerlifting: eligible
- Olympic weightlifting: eligible, usually manual/special-pattern review
- strongman: eligible, usually manual/special-pattern review
- stretching: not eligible
- cardio: not eligible
- plyometrics: not counted in ordinary resistance-set totals in v0.1

Non-eligible exercises retain their complete upstream record.

## FEDB++ muscle ontology

The 17 upstream groups are retained, with normalized underscore keys where needed:

- abdominals
- abductors
- adductors
- biceps
- calves
- chest
- forearms
- glutes
- hamstrings
- lats
- lower_back
- middle_back
- neck
- quadriceps
- shoulders
- traps
- triceps

FEDB++ adds three groups that the upstream ontology cannot represent cleanly:

- tibialis
- rotator_cuff
- hip_flexors

We deliberately keep the ontology coarse in v0.1.

## Canonical movement patterns

Initial patterns include:

### Pressing/pulling
`horizontal_press`, `incline_press`, `decline_press`, `vertical_press`,
`horizontal_pull`, `vertical_pull`, `dip_chest_bias`, `dip_triceps_bias`,
`shrug`, `reverse_fly`

### Shoulder/arm
`shoulder_abduction`, `shoulder_flexion`, `shoulder_extension`,
`shoulder_external_rotation`, `shoulder_internal_rotation`,
`elbow_flexion`, `elbow_flexion_brachioradialis_bias`,
`elbow_extension`, `wrist_flexion`, `wrist_extension`, `grip`

### Lower body
`squat`, `squat_quad_bias`, `squat_glute_bias`, `lunge`, `step_up`,
`knee_extension`, `knee_flexion`, `hip_hinge`, `hip_extension`,
`hip_abduction`, `hip_adduction`,
`plantar_flexion_straight_knee`, `plantar_flexion_bent_knee`,
`dorsiflexion`

### Trunk/integrated
`trunk_flexion`, `trunk_extension`, `trunk_rotation`, `lateral_flexion`,
`anti_extension`, `anti_rotation`, `loaded_carry`, `farmer_carry`,
`sled_push`, `sled_pull`, `jump`, `kettlebell_swing`,
`olympic_first_pull`, `olympic_second_pull`, `olympic_catch`,
`olympic_overhead_catch`, `neck_flexion`, `neck_extension`

## Initial pattern defaults

| Pattern | Direct | Indirect | Stabilizers |
|---|---|---|---|
| horizontal_press | chest | triceps, shoulders | — |
| incline_press | chest, shoulders | triceps | — |
| decline_press | chest | triceps, shoulders | — |
| vertical_press | shoulders | triceps | abdominals |
| horizontal_pull | middle_back, lats | biceps, shoulders | forearms |
| vertical_pull | lats | biceps, middle_back | forearms |
| shrug | traps | — | forearms |
| reverse_fly | shoulders, middle_back | traps | — |
| shoulder_abduction | shoulders | traps | — |
| elbow_flexion | biceps | forearms | — |
| elbow_flexion_brachioradialis_bias | biceps, forearms | — | — |
| elbow_extension | triceps | — | — |
| squat | quadriceps, glutes | adductors | lower_back, hamstrings, calves |
| squat_quad_bias | quadriceps | glutes, adductors | lower_back |
| squat_glute_bias | glutes, quadriceps | adductors | lower_back |
| lunge | quadriceps, glutes | adductors | hamstrings, calves |
| step_up | quadriceps, glutes | adductors | calves |
| knee_extension | quadriceps | — | — |
| knee_flexion | hamstrings | calves | — |
| hip_hinge | hamstrings, glutes | — | lower_back, forearms |
| hip_extension | glutes | hamstrings | lower_back |
| hip_abduction | abductors | glutes | — |
| hip_adduction | adductors | — | — |
| plantar flexion | calves | — | — |
| trunk_flexion | abdominals | — | — |
| trunk_extension | lower_back | glutes, hamstrings | — |
| trunk_rotation | abdominals | — | — |
| lateral_flexion | abdominals | — | — |
| farmer_carry | forearms, traps | — | abdominals, lower_back |
| kettlebell_swing | glutes, hamstrings | — | lower_back, forearms |
| jump | quadriceps, glutes, calves | hamstrings | — |

## Important classification decisions

### Bench press

Ordinary horizontal bench press:

- direct: chest
- indirect: triceps, shoulders

Close-grip variants may promote triceps to direct.

### Squat

Ordinary squat:

- direct: quadriceps, glutes
- indirect: adductors
- stabilizer: hamstrings, lower_back, calves

FEDB++ does not award a hamstring indirect set merely because hamstrings are active in a squat.

### Row

Typical row:

- direct: middle_back, lats
- indirect: biceps, shoulders
- stabilizer: forearms
- unsupported bent-over variants may additionally mark lower_back as stabilizer

### Pull-up / pulldown

- direct: lats
- indirect: biceps, middle_back
- stabilizer: forearms

A supinated chin-up may be separately reviewed for biceps direct status.

### Romanian/stiff-leg deadlift

- direct: hamstrings, glutes
- stabilizer: lower_back, forearms

### Conventional deadlift

- direct: glutes, hamstrings
- indirect: quadriceps
- stabilizer: lower_back, traps, forearms, lats

This intentionally differs from an involved-muscles taxonomy.

## Rule precedence

The converter uses this order:

1. normalize source labels;
2. decide volume eligibility;
3. apply explicit exercise-ID override;
4. infer movement pattern(s);
5. apply pattern defaults;
6. apply variant/modifier logic;
7. if isolation exercise remains unrecognized:
   - primary → direct
   - secondary → indirect
   - confidence medium
8. if compound exercise remains unrecognized:
   - primary → direct
   - secondary → indirect
   - confidence low
   - review reason added
9. ensure role arrays are mutually exclusive;
10. preserve original source record.

Explicit reviewed overrides always beat generic rules.

## Confidence and review

- `high`: well-defined pattern or reviewed override
- `medium`: reasonable rule classification with some uncertainty
- `low`: fallback or ambiguous compound movement

The purpose of confidence is not to hide uncertainty; it is to expose it so independent reviewers can focus effort where it matters.

## Reproducibility

Dataset metadata records:

- schema version
- converter version
- generation timestamp
- upstream URL
- source SHA-256
- source exercise count
- output exercise count
- completeness status
- default set credits

Each exercise retains its unmodified source record.

## JSON Schema

`free-exercise-db-plusplus.schema.json` is the normative structural contract.

It can verify:
- required fields
- legal role names/muscle names
- metadata shape
- confidence values
- uniqueness of arrays
- expected source structure

It cannot prove semantic biomechanics. That remains subject to design rules and independent review.

## Known v0.1 limitations

- keyword-based pattern inference;
- incomplete treatment of unusual strongman/Olympic/multi-phase movements;
- no technique, ROM, load, effort, tempo, or individual-anthropometry model;
- coarse muscle groups;
- default 0.5 indirect credit is configurable and not asserted as a biological constant;
- ambiguous exercises are intentionally surfaced for review rather than assigned false precision.

## Design principle

Prefer transparent, reproducible assumptions and explicit uncertainty over hidden heuristics or false precision.
