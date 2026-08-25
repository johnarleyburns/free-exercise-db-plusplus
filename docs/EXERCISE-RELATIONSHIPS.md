# Exercise families and relationships

v1.5 adds an optional, deterministic relationship artifact over stable DB++
exercise IDs. A record is structurally:

```text
Barbell_Bench_Press_-_Medium_Grip → bench_press → Dumbbell_Bench_Press
```

The artifact records curated family membership and normalized dimensions such
as equipment, grip, stance, angle, laterality, body position, load position,
assistance, and resistance type. Pairwise relationships are derived at query
time from shared reviewed membership and inspectable dimensions, avoiding an
O(N²) published graph. Families are descriptive
taxonomy, not physiological equivalence, automatic substitutions, or a
recommendation/ranking system. Muscle coverage differences use the existing
DB++ direct/indirect/stabilizer set-credit semantics only.

The artifact has its own schema version (`0.1.0`) and can be loaded with
`fedbpp.RelationshipRegistry`. Unassigned exercises are intentional and are
reported for review. Family assignments derive from reviewed source metadata,
deterministic rules, and explicit overrides; provenance does not claim
scientific evidence for taxonomy.

Boundary decisions include separate `pull_up` and `chin_up` families,
`romanian_deadlift` separate from `deadlift`, and exclusion of `upright_row`
from the horizontal `row` family. Push-ups, chest presses, and bench presses
are not merged merely because they share muscles.

## Normative model

- Exercise identity is the stable DB++ `exerciseId`.
- A family is a flat, stable, snake-case identifier between movement pattern
  and specific exercise. Families do not have parents in schema 0.1.0.
- Every accepted assignment has `high` or `medium` confidence and taxonomy
  provenance. Low-confidence candidates remain review output only.
- The relationship vocabulary is `member_of_family`, `variation_of`,
  `equipment_variant_of`, `grip_variant_of`, `stance_variant_of`,
  `angle_variant_of`, and `laterality_variant_of`.
- The main exercise database remains the source of truth for equipment and
  movement/muscle metadata. Semantic validation rejects contradictions.

Compatible 0.1.x changes may add reviewed assignments or optional metadata
without changing existing family identifiers. Family identifiers are never
silently recycled. Breaking artifact changes require an independent schema
version change, not merely a project release change.

## Reviewed boundaries

- Pull-ups and chin-ups are separate families.
- Front, back, hack, box, and other named squats remain in `squat` with medium
  confidence. Squat jerks, jerk-dip drills, Turkish get-ups, and
  stretching-only split squats are excluded.
- Conventional, sumo, trap-bar, strongman, and named deadlift derivatives are
  in `deadlift` with medium confidence. Romanian deadlifts are separate;
  good mornings and stiff-legged variants are not forced into either family.
- Hip thrust and glute bridge remain separate families.
- Horizontal rows are `row`; upright rows are excluded.
- Arnold presses remain shoulder-press variants with medium confidence.
- Push-ups and generic machine/cable chest presses are not bench presses.
- Olympic lifts, mobility, stretching, and unrelated strongman events are not
  grouped solely by shared patterns or muscles.

Complete reviewed membership for the central families is frozen in
`tests/relationships/golden-families.json`.

## Python and CLI

```python
from fedbpp import Database, RelationshipRegistry

db = Database.load("free-exercise-db-plusplus.json")
registry = RelationshipRegistry.load(db=db)
family = registry.family_for("Dumbbell_Bench_Press")
members = registry.exercises_in_family("bench_press")
structure = registry.compare_exercises(
    "Barbell_Bench_Press_-_Medium_Grip", "Dumbbell_Bench_Press"
)
coverage = registry.compare_exercise_coverage(
    "Barbell_Bench_Press_-_Medium_Grip", "Dumbbell_Bench_Press"
)
```

CLI commands are `family`, `family-members`, `related`, and
`compare-exercises`. PLAN commands accept optional `--relationships` data.
Related results are discovery candidates, never recommended substitutions.

Examples from the published database include barbell vs dumbbell bench press
(equipment), flat vs incline bench press (angle), and regular vs wide-stance
squat (stance). Pull-up vs chin-up are different families. Upright row vs
bent-over row are not related by the v1.5 family model.

## Interoperability boundary

`family-interop-mapping.schema.json` permits a genuinely broad external
concept to target a family without selecting an arbitrary exercise. Exact
external identities continue to target exercises. The reviewed Garmin subset
contains sixteen exact mappings and no verified broad family identifier, so no
family mapping is invented.

## Scientific claim boundary

Relationships do not establish equal hypertrophy, strength adaptation,
fatigue, injury risk, motor learning, difficulty, or interchangeability.
Coverage differences use only existing DB++ roles and set credits. No magic
similarity, recommendation, or substitution score is defined in v1.5.
