# Free Exercise DB++ Roadmap

Status: **v1.5.0 release preparation**
Current stable release: **v1.4.1**
Next milestone: v1.5 exercise relationships, families, and variations

## v1.5 implementation status

The separate relationship artifact, schema, deterministic generator, curated
family rules/overrides, validation, reports, Python API, CLI, optional plan
family views, substitution context, honest family-level interop contract,
isolated-wheel support, and Swift/Kotlin/R readers are implemented. The stable
v1.0-v1.4.1 contracts remain unchanged.

## v1.3 implementation status

Operational conversion is implemented for FHIR R4 Physical Activity Bundle JSON,
including strict/lossy modes, provenance, deterministic output, custom exercise
preservation, the installed Python API, and the `fedbpp` CLI. Garmin FIT binary
and platform API integrations remain bounded/optional as documented.

## v1.2 implementation status

The interoperability audit, schemas, structural mappings, Health Connect crosswalk, coverage report, validator/registry, Python API, and documentation are implemented. Binary/API import/export remains explicitly deferred to v1.3.

## 1. Direction

Free Exercise DB++ now has a stable three-layer foundation:

```text
Exercise vocabulary
        ↓
PLAN → ACTUAL → TARGET
        ↓
deterministic analysis
```

v1.0 established the exercise vocabulary. v1.1 stabilized PLAN, ACTUAL, TARGET, and analysis semantics. Future work should treat those semantics as stable unless real-world interoperability exposes a genuine defect.

The project should now evolve into an open strength/resistance-training interoperability ecosystem:

```text
Garmin FIT ───────────┐
Health Connect ───────┤
HealthKit ────────────┤
FHIR ─────────────────┼──→ mapping/import layer
IEEE/Open mHealth ────┘            ↓
                         Free Exercise DB++
                                ↓
                         PLAN / ACTUAL / TARGET
                                ↓
                         deterministic analysis
                                ↓
                       trainer/research workflows
```

Core rule:

> **Do not distort the DB++ canonical model merely to fit an external format.**

External standards may be less expressive. Mapping loss must be explicit, testable, and auditable rather than silently discarded.

---

# 2. Stable foundation

## v1.0 — Exercise vocabulary

Consider stable:

- `exerciseId` vocabulary;
- normalized Free Exercise DB data;
- direct / indirect / stabilizer roles;
- movement patterns and taxonomy;
- genre and exercise metadata;
- JSON Schema;
- provenance/evidence metadata;
- deterministic generated artifact.

Existing exercise IDs should remain stable.

## v1.1 — PLAN / ACTUAL / TARGET / ANALYSIS

Consider semantically stable:

- Workout ACTUAL;
- Workout PLAN;
- volume TARGET profiles;
- PLAN coverage;
- direct / indirect / stabilizer / effective-set analysis;
- authoritative `metadata.setCredits`;
- `dbpp-default-volume-v1`;
- arbitrary cycle lengths and seven-day normalization;
- min / target / max and partial ranges;
- phase-specific cycles and periodization;
- duration-weighted phase analysis;
- PLAN-vs-PLAN;
- exercise, muscle, and movement-pattern exposure frequency;
- PLAN-vs-ACTUAL;
- substitutions and `setPrescriptionId`;
- unplanned ACTUAL work;
- strict/substitution-adjusted adherence;
- load / RPE / RIR adherence where meaningful;
- mass-based volume-load adherence;
- TARGET gap analysis;
- deterministic research exports;
- analysis provenance.

Changes that alter v1.1 numerical results should require a demonstrated defect, documentation, regression fixtures, and an explicit compatibility/version decision.

---

# 3. v1.2.0 — Interoperability Mapping

## Objective

Create a rigorous, machine-readable mapping layer between DB++ and major fitness/health ecosystems.

The first goal is **mapping knowledge, not exporters**.

Before implementing adapters, establish:

- what each ecosystem represents;
- external exercise identity;
- exact field mappings;
- required conversions;
- unsupported DB++ concepts;
- external concepts DB++ cannot represent;
- mapping loss;
- provenance;
- round-trip expectations.

Initial ecosystems, subject to audit findings:

1. Garmin FIT;
2. Android Health Connect;
3. Apple HealthKit;
4. HL7 FHIR Physical Activity;
5. IEEE 1752.1 / Open mHealth;
6. Google Fit legacy exercise vocabulary as a historical crosswalk where useful.

---

# 4. v1.2 Phase A — Standards audit

Create:

```text
docs/interop/
  README.md
  GARMIN-FIT.md
  HEALTH-CONNECT.md
  HEALTHKIT.md
  FHIR.md
  IEEE-1752-1.md
  GOOGLE-FIT-LEGACY.md
  COMPATIBILITY-MATRIX.md
```

For each ecosystem document:

- authoritative specification/source;
- reviewed version/date;
- exercise/activity identity;
- workout/session model;
- exercise-block model;
- set representation;
- reps;
- load/resistance;
- units;
- duration/distance;
- rest;
- RPE/RIR;
- tempo;
- set type;
- laterality;
- completion;
- substitutions;
- PLAN vs ACTUAL distinction;
- workout plans/routines;
- periodization;
- provenance/source metadata;
- timestamps/time zones;
- participant identity;
- custom fields/extensions;
- round-trip limitations.

Classify each DB++ concept:

```text
lossless
representable_with_conversion
representable_with_extension
lossy
unsupported
not_applicable
unknown
```

Do not infer support merely because a format has generic metadata.

---

# 5. Compatibility matrix

Build one human-readable and, where useful, machine-readable matrix covering:

```text
DB++ concept | Garmin FIT | Health Connect | HealthKit | FHIR | IEEE/Open mHealth | Notes
```

It must answer:

- Can bench press be identified distinctly?
- Can sets have independent reps/load?
- Are warmup and working sets distinguishable?
- Can RPE/RIR be represented?
- Can planned sets be represented?
- Can ACTUAL link to PLAN?
- Can custom exercises survive?
- Can DB++ `exerciseId` survive?
- Can provenance survive?
- Is round-trip lossless?

Cover exercise definitions, ACTUAL, PLAN, TARGET where relevant, and provenance.

---

# 6. Mapping registry

Expand the existing interop mapping architecture into a first-class public artifact.

Possible structure:

```text
mappings/
  registry.json
  garmin-fit.json
  health-connect.json
  healthkit.json
  fhir.json
  ieee-1752-1.json
  google-fit-legacy.json
```

Prefer evolving `interop-mapping.schema.json` over inventing a competing contract.

A mapping should capture at least:

```text
exerciseId
external system
external identifier
relation
direction
confidence
notes
provenance
```

Normative relation vocabulary:

```text
exact
close
broader
narrower
approximate
unmapped
```

Define each term precisely. Do not call mappings exact merely because names are similar.

Mappings may be directional. External → DB++ can be deterministic while DB++ → external may collapse several exercises into one broader concept.

---

# 7. Mapping provenance and validation

Mappings should record, where practical:

```text
external specification/version
external identifier
source/reference
review date
mapping method
relation
confidence
notes
```

CI must validate:

- every DB++ `exerciseId`;
- relation/direction vocabulary;
- required provenance;
- duplicate/conflicting mappings;
- external uniqueness constraints;
- schema validity;
- deterministic registry generation.

Generate reports:

```text
total DB++ exercises
exact / close / approximate / unmapped
external concepts without mappings
coverage by genre
coverage by movement pattern
coverage by equipment
```

Never count approximate mappings as exact coverage.

---

# 8. v1.2 Phase B — Exercise crosswalks

Exercise identity comes before workout serialization.

For each ecosystem:

1. enumerate the external strength vocabulary;
2. normalize labels for review;
3. generate mapping candidates;
4. manually review ambiguity;
5. map to stable DB++ IDs;
6. classify relation/direction/confidence;
7. add provenance;
8. add regression tests;
9. generate coverage reports.

Fuzzy/string matching may assist offline candidate generation, but published/runtime mappings must be deterministic. No fuzzy matching by default.

---

# 9. v1.2 Phase C — Workout field mappings

Once exercise identity is understood, define external workout ↔ DB++ ACTUAL mappings.

For every field document:

```text
source
destination
conversion
units
loss behavior
fallback
provenance
round-trip expectation
```

Cover:

- session ID;
- timestamps;
- exercise ID/custom identity;
- set order;
- reps;
- load/unit;
- duration/distance;
- RPE/RIR;
- rest;
- set type;
- completion;
- notes;
- source provenance;
- PLAN linkage if available.

Never manufacture unavailable values.

---

# 10. Loss reporting

Design a reusable loss model before operational exporters.

Example:

```json
{
  "mappingStatus": "lossy",
  "losses": [
    {
      "path": "exercises[0].sets[1].rir",
      "reason": "destination format has no RIR representation"
    }
  ]
}
```

Potential severities:

```text
informational
lossy
unsupported
invalid
```

Converters must not silently discard meaningful known information.

---

# 11. Round-trip fixtures

Test:

```text
external → DB++ ACTUAL → external
DB++ ACTUAL → external → DB++ ACTUAL
```

Classify fixtures:

```text
lossless
normalized
expected_lossy
unsupported
```

Tests should assert expected losses, not merely successful serialization.

---

# 12. v1.2 deliverables

Target:

- standards audit;
- compatibility matrix;
- evolved mapping schema if necessary;
- machine-readable mapping registry;
- at least one production-quality external exercise crosswalk;
- provenance;
- coverage reports;
- validation tooling;
- loss model;
- round-trip framework;
- mapping lookup API;
- Python mapping API;
- Swift lookup support if practical;
- consumer documentation.

Do **not** require five shallow exporters. One strong mapping foundation is more valuable.

Possible slicing:

```text
v1.2.0  framework + first production mapping
v1.2.1  corrections/coverage
v1.2.2+ additional ecosystem mappings
```

---

# 13. v1.3.0 — Import/export tooling and CLI

## Objective

Turn mapping knowledge into operational interchange.

Potential CLI:

```bash
fedbpp validate workout.json
fedbpp validate plan.json
fedbpp analyze-plan plan.json
fedbpp compare-plans a.json b.json
fedbpp compare-actual plan.json workout.json
fedbpp gaps plan.json target.json

fedbpp import fit workout.fit -o workout.json
fedbpp export fit workout.json -o workout.fit
fedbpp export fhir workout.json -o observation.json
```

Syntax is illustrative, not contractual.

Importer architecture:

```text
external input
→ parser
→ normalized external representation
→ mapping registry
→ DB++ ACTUAL
→ validation
→ loss/provenance report
```

Exporter:

```text
DB++ ACTUAL/PLAN
→ validation
→ mapping registry
→ destination capability analysis
→ loss report
→ external representation
→ serializer
```

Consider explicit modes:

```text
strict
allow-lossy
```

Strict conversion should fail when meaningful information cannot be represented. Lossy mode may proceed only with explicit diagnostics.

The CLI must call the canonical analysis implementation rather than duplicate algorithms.

---

# 14. v1.3 acceptance criteria

Every advertised format requires:

- documented supported version;
- deterministic exercise mapping;
- field compatibility matrix;
- loss reporting;
- provenance;
- golden fixtures;
- malformed-input tests;
- round-trip tests;
- documented limitations;
- deterministic output.

Actual format priority should be decided from v1.2 findings, with Garmin FIT the initial candidate rather than a commitment.

---

# 15. v1.4.0 — Longitudinal research/trainer workflows

## Objective

Analyze subjects across time rather than only individual PLAN/session comparisons.

Conceptual hierarchy:

```text
subject
  ├── PLAN revisions
  ├── ACTUAL sessions
  ├── TARGET profiles
  └── analysis periods
```

Support periods such as:

```text
calendar week
rolling 7 days
plan cycle
phase
mesocycle
custom date range
```

Always distinguish native plan-cycle, calendar, and normalized-seven-day metrics.

Enable questions such as:

- prescribed vs completed volume over 12 weeks;
- direct/indirect adherence;
- missed sessions;
- unplanned work;
- muscles repeatedly below TARGET;
- exposure-frequency changes;
- substitutions by phase;
- actual vs periodized plan.

Keep analysis descriptive; avoid unsupported causal/physiological claims.

---

# 16. Research table model

Primary tidy grain:

```text
subject × period × muscle
```

Candidate fields:

```text
subject_id
period_start
period_end
plan_id
revision_id
phase_id
muscle

planned_direct_min/target/max
actual_direct
planned_indirect_min/target/max
actual_indirect
planned_effective_min/target/max
actual_effective

planned_exposures
actual_exposures
strict_adherence
substitution_adjusted_completion

target_min/target/max
target_state
mapped_fraction

analysis_policy
db_schema_version
db_converter_version
```

Also provide exercise- and session-level tables.

CSV remains baseline. Parquet can be optional later; it should not become a core dependency.

---

# 17. Missing-data semantics and privacy

Distinguish:

```text
zero
not prescribed
not recorded
unknown
unmapped
volume-ineligible
not applicable
```

Never collapse these to zero.

Use opaque subject IDs. DB++ should not require names, email, DOB, or other personally identifying data.

v1.4 deliverables may include:

- longitudinal analysis API;
- analysis-period model;
- planned/actual aggregation;
- TARGET aggregation;
- session adherence;
- subject-period-muscle tables;
- exercise/session tables;
- missing-data specification;
- Python/CLI support;
- R-friendly output;
- golden longitudinal fixtures.

---

# 18. v1.5.0 — Exercise relationships and families

## Objective

Add a descriptive relationship layer above stable exercise IDs.

Do not replace IDs.

Potential relationships:

```text
family
variation_of
equipment_variant_of
grip_variant_of
stance_variant_of
incline_variant_of
unilateral_variant_of
progression_related
regression_related
```

Be conservative with `substitute_for` and `equivalent_to`.

Use cases:

- browse variants;
- family-level frequency;
- family-level PLAN comparison;
- identify structural relationships;
- candidate substitutions for applications;
- map broad external vocabularies to DB++.

Do not automatically treat family members as physiologically equivalent.

Substitution analysis should distinguish:

```text
structural similarity
movement-pattern similarity
muscle-coverage similarity
equipment compatibility
explicit trainer/user substitution
```

ACTUAL substitution linkage should remain explicit rather than inferred automatically.

---

# 19. v2.0 — Optional advanced anatomy/evidence

Only after interoperability, longitudinal research, and relationships mature.

Possible optional anatomy:

```text
pectoralis major → clavicular / sternocostal
deltoid → anterior / lateral / posterior
triceps → long / lateral / medial
```

Requirements before adoption:

- evidence standard;
- ontology;
- provenance;
- support for the chosen granularity;
- distinction between anatomical participation and hypertrophy claims;
- compatibility with broad-muscle analysis;
- avoidance of false precision.

The broad direct=1.0 / indirect=0.5 model remains available.

---

# 20. Cross-language strategy

Python remains the reference implementation for advanced analysis/conversion.

Swift, Kotlin, and R should support portable contracts according to real demand.

Priority:

```text
JSON/schema compatibility
mapping lookup
core coverage
platform-specific integration
advanced parity where justified
```

Do not block useful reference functionality on simultaneous full parity, but never claim parity that does not exist.

---

# 21. Schema and version strategy

Maintain distinct contracts:

```text
free-exercise-db-plusplus.schema.json
workout.schema.json
workout-plan.schema.json
volume-target.schema.json
interop-mapping.schema.json
```

Potential future schemas only when justified:

```text
mapping-loss.schema.json
exercise-relationship.schema.json
research-analysis.schema.json
```

Distinguish:

```text
project release
DB schema
converter
Workout schema
PLAN schema
TARGET schema
mapping schema
analysis policy
mapping dataset version
```

Do not bump every version when the project release changes.

Prefer additive evolution.

Never silently rename/recycle exercise IDs, reinterpret analysis policies, change credits/ranges, or change mapping meaning.

---

# 22. Development principles

## Data first

For interoperability and relationships:

```text
research
→ model/schema
→ curated data
→ validation
→ reports
→ fixtures
→ API
→ CLI/exporter
```

## Determinism

Public generated artifacts remain deterministic.

CI should verify:

- provenance;
- schema validity;
- stable ordering;
- reproducible generation;
- mapping validity;
- fixtures;
- packages;
- release checksums.

## Interop quality gate

Do not advertise support because a serializer exists.

Require:

- authoritative standard reviewed;
- supported version documented;
- exercise mapping;
- compatibility matrix;
- loss model;
- provenance;
- fixtures;
- malformed-input tests;
- round-trip tests;
- limitations;
- deterministic output.

---

# 23. Explicit non-goals

Unless separately approved:

- runtime AI/fuzzy exercise matching;
- silent fuzzy matching;
- medical recommendations;
- injury-risk prediction;
- automatic hypertrophy prescriptions;
- automatic program generation;
- universal stimulus scores;
- RPE/RIR-derived physiological weighting;
- unsupported exercise-equivalence claims;
- mandatory cloud services;
- user accounts;
- personally identifying athlete records;
- proprietary lock-in.

DB++ remains an open portable data/interchange project.

---

# 24. Immediate implementation plan

## Milestone 1 — Standards audit

Research authoritative:

1. Garmin FIT strength model;
2. Android Health Connect;
3. Apple HealthKit;
4. HL7 FHIR Physical Activity;
5. IEEE 1752.1/Open mHealth.

Document supported versions and build:

```text
docs/interop/COMPATIBILITY-MATRIX.md
```

Do not change schemas prematurely.

## Milestone 2 — Mapping framework

Audit/evolve `interop-mapping.schema.json`.

Define:

- relations;
- directionality;
- confidence;
- provenance;
- loss model;
- validation;
- deterministic registry/index.

## Milestone 3 — First crosswalk

Select the ecosystem with the best mix of usefulness, documentation, strength detail, and feasibility. Garmin FIT is the initial candidate, subject to the audit.

Build:

```text
external vocabulary
→ reviewed DB++ mapping
→ coverage report
→ regression tests
```

## Milestone 4 — Workout mapping

Map external workouts to DB++ ACTUAL with explicit conversion/loss rules and fixtures.

## Milestone 5 — v1.2 release

Ship the mapping framework plus at least one production-quality crosswalk.

---

# 25. Definitions of success

## v1.2

A third-party developer can:

1. load DB++;
2. resolve an external exercise ID deterministically;
3. inspect exact/close/approximate relation;
4. inspect provenance;
5. understand ACTUAL field compatibility;
6. detect expected information loss;
7. implement an adapter using documented fixtures;
8. do so without reading DB++ implementation source.

## v1.3

A user can import/export a supported workout with explicit provenance/loss reporting.

## v1.4

A trainer/researcher can analyze many ACTUAL sessions against PLAN/TARGET across periods and obtain deterministic tidy datasets.

## v1.5

Applications can navigate exercise families/variations without changing stable IDs or claiming automatic equivalence.

---

# 26. Maintainer decision test

Before adding a feature ask:

1. Is it a portable data/interchange concern?
2. Does it strengthen exercise identity, PLAN, ACTUAL, TARGET, analysis, mapping, or reproducibility?
3. Are semantics deterministic?
4. Can it be validated?
5. Can it be tested with golden/hand-calculated fixtures?
6. Does it preserve stable contracts?
7. Are we representing known information rather than inventing physiological meaning?

Prefer interoperability, reproducibility, and inspectability.

---

# 27. Next action

Begin **v1.2 Phase A — Standards Audit**.

Do **not** start by coding exporters.

First produce:

```text
docs/interop/COMPATIBILITY-MATRIX.md
docs/interop/GARMIN-FIT.md
docs/interop/HEALTH-CONNECT.md
docs/interop/HEALTHKIT.md
docs/interop/FHIR.md
docs/interop/IEEE-1752-1.md
```

Then audit `interop-mapping.schema.json` against the standards research.

Only after that should the project commit to the first production mapping implementation.
