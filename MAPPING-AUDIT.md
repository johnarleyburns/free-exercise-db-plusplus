# DB++ Exercise-Specific Mapping Audit

- Audited non-high volume mappings: **109**
- Upstream primary/secondary fallbacks: **24**
- Indirect-evidence pattern mappings: **13**
- Complex-supported pattern mappings: **72**

## Remaining fallbacks

| Exercise | Mechanic | Source primary | Source secondary | DB++ direct | DB++ indirect |
|---|---|---|---|---|---|
| Alternating Deltoid Raise | isolation | shoulders |  | shoulders |  |
| Car Drivers | isolation | shoulders | forearms | shoulders | forearms |
| Crucifix | isolation | shoulders | forearms | shoulders | forearms |
| Downward Facing Balance | isolation | glutes | abdominals, hamstrings | glutes | abdominals, hamstrings |
| Dumbbell Lying Pronation | isolation | forearms |  | forearms |  |
| Dumbbell Lying Supination | isolation | forearms |  | forearms |  |
| Isometric Neck Exercise - Front And Back | isolation | neck |  | neck |  |
| Isometric Neck Exercise - Sides | isolation | neck |  | neck |  |
| Leg Lift | isolation | glutes | hamstrings | glutes | hamstrings |
| Lying Face Down Plate Neck Resistance | isolation | neck |  | neck |  |
| Lying Face Up Plate Neck Resistance | isolation | neck |  | neck |  |
| One-Legged Cable Kickback | isolation | glutes | hamstrings | glutes | hamstrings |
| Plate Pinch | isolation | forearms |  | forearms |  |
| Power Partials | isolation | shoulders |  | shoulders |  |
| Reverse Machine Flyes | isolation | shoulders |  | shoulders |  |
| Seated Head Harness Neck Resistance | isolation | neck |  | neck |  |
| Single Dumbbell Raise | isolation | shoulders | forearms, traps | shoulders | forearms, traps |
| Smith Incline Shoulder Raise | isolation | shoulders | chest | shoulders | chest |
| Standing Dumbbell Straight-Arm Front Delt Raise Above Head | isolation | shoulders |  | shoulders |  |
| Standing Front Barbell Raise Over Head | isolation | shoulders |  | shoulders |  |
| Standing Low-Pulley Deltoid Raise | isolation | shoulders | forearms | shoulders | forearms |
| Standing Olympic Plate Hand Squeeze | isolation | forearms | biceps | forearms | biceps |
| Wrist Roller | isolation | forearms | shoulders | forearms | shoulders |
| Wrist Rotations with Straight Bar | isolation | forearms |  | forearms |  |

## Indirect-support mappings

| Exercise | Pattern | Direct | Indirect | Source-only | DB++-only |
|---|---|---|---|---|---|
| Backward Drag | sled_pull | quadriceps, glutes | hamstrings, calves | lower back |  |
| Bear Crawl Sled Drags | sled_pull | quadriceps, glutes | hamstrings, calves |  | forearms |
| Bent Press | bent_press | abdominals, shoulders | glutes, hamstrings, triceps | lower back | lower_back |
| Face Pull | face_pull | shoulders, middle_back | traps, biceps | middle back | biceps, forearms, middle_back, traps |
| Kipping Muscle Up | muscle_up | lats, chest, triceps | biceps, shoulders, middle_back | middle back, traps | chest, middle_back |
| Muscle Up | muscle_up | lats, chest, triceps | biceps, shoulders, middle_back | middle back, traps | chest, middle_back |
| One-Arm Medicine Ball Slam | medicine_ball_slam | abdominals, lats | shoulders |  | glutes, quadriceps |
| Pallof Press | anti_rotation | abdominals |  | chest, shoulders, triceps |  |
| Pallof Press With Rotation | anti_rotation | abdominals |  | chest, shoulders, triceps |  |
| Rope Climb | rope_climb | lats, biceps, forearms | middle_back | middle back, shoulders | abdominals, middle_back |
| Sled Drag - Harness | sled_pull | quadriceps, glutes | hamstrings, calves |  | forearms |
| Sled Overhead Backward Walk | sled_pull | quadriceps, glutes | hamstrings, calves | middle back, shoulders | forearms, glutes, hamstrings |
| Spider Crawl | spider_crawl | abdominals | shoulders, chest, triceps |  | glutes |
