# ADR 0011: Exercise relationships are a separate enrichment artifact

Status: Accepted for v1.5.0

The canonical relationship layer is published in `exercise-relationships.json`
and validated by `exercise-relationships.schema.json`. It is not embedded in
the stable exercise-definition database. This preserves the v1.0-v1.4.1
database contract, permits richer provenance and graph validation, and lets
consumers opt in. The packaged Python wheel includes the artifact.

Families are flat, curated groupings between movement pattern and exercise ID.
Relationships are descriptive taxonomy; they do not establish equivalence,
substitution advice, hypertrophy, fatigue, injury risk, or any other
physiological conclusion. Existing explicit PLAN/ACTUAL substitutions remain
authoritative.
