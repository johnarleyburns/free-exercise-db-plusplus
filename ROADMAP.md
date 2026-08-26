# Free Exercise DB++ Roadmap

Status: **post-v1.5.1 planning**  
Current stable release: **v1.5.1**  
Primary product direction: **Trainer/client planning, self-coaching, and automated coaching built on a deterministic training-domain engine**

---

# 1. Product vision

Free Exercise DB++ should evolve from an exercise vocabulary and workout-analysis toolkit into a **portable, deterministic training-domain engine** that can sit underneath trainer software, self-coaching applications, research workflows, and automated-coach systems.

The intended architectural boundary is:

```text
Application/Product Layer
  UI, accounts, messaging, notifications,
  persistence, sync, billing, permissions
                |
                v
Free Exercise DB++
  exercise vocabulary
  relationships/families
  PLAN / ACTUAL / TARGET
  longitudinal history
  plan evaluation
  training-state derivation
  progression policies
  plan generation
  coaching decisions
  adaptation
  provenance/explanations
  interoperability
```

Free Exercise DB++ should own training-domain semantics and deterministic decision logic.

Applications should own presentation, identity, messaging, storage, synchronization, and product-specific workflows.

The same engine should support trainer→client, self-coached, trainer-assisted generation, and automated coaching.

# 2. Stable foundation through v1.5.1

Treat as stable:

- v1.0 exercise vocabulary and stable exerciseId
- v1.1 PLAN / ACTUAL / TARGET / analysis
- v1.2 interoperability mappings
- v1.3 operational conversion + CLI
- v1.4.1 longitudinal analysis
- v1.5.1 exercise relationships/families

Do not casually redesign these semantics.

# 3. New release sequence

```text
v1.6  Training Profile + Plan Evaluation
v1.7  Training State + Progression Policies
v1.8  Deterministic Plan Generation
v1.9  Adaptive Coaching / Plan Revision Engine
v2.0+ Optional advanced physiology/anatomy,
      richer evidence layers, more standards
```

Core rule:

> Evaluate before generating. Derive state before adapting. Explain every automated decision.

# 4. Core operating modes

Trainer/client:

```text
Trainer -> PLAN -> assignment -> Client -> ACTUAL -> feedback -> revised PLAN
```

Self-coached:

```text
User -> TrainingProfile + TARGET -> PLAN -> ACTUAL -> evaluation -> revised PLAN
```

Automated coach:

```text
Profile + TARGET + History -> TrainingState -> Generator -> PLAN -> ACTUAL -> CoachDecision -> revised PLAN
```

Use one domain model for all three.

# 5. v1.6 — Training Profile + Plan Evaluation

Implementation status: complete in the Python reference package. See
`docs/TRAINING-PROFILE.md`, `docs/PLAN-EVALUATION.md`, and ADRs 0012–0016.

## Objective

Formalize goals, constraints, preferences, equipment, and availability, then add deterministic `evaluate_plan()`.

The evaluator must answer whether a PLAN satisfies:

- muscle-volume targets
- frequency targets
- movement-pattern coverage
- family coverage
- available equipment
- exercise/family exclusions
- session count constraints
- approximate duration constraints
- soft preferences

It should return exact gaps, not a vague score.

## TrainingProfile

Likely portable artifact:

```text
training-profile.schema.json
```

Conceptual shape:

```json
{
  "schemaVersion": "0.1.0",
  "profileId": "profile-123",
  "subjectId": "subject-42",
  "goals": [
    {"type": "hypertrophy", "priority": 1},
    {"type": "strength", "priority": 2}
  ],
  "experience": "intermediate",
  "availability": {
    "cycleLengthDays": 7,
    "sessionsPerCycle": {"min": 3, "target": 4, "max": 4},
    "minutesPerSession": {"max": 60}
  },
  "equipment": ["barbell", "dumbbell", "cable", "machine"],
  "exercisePreferences": {
    "preferredExerciseIds": [],
    "avoidedExerciseIds": [],
    "preferredFamilyIds": [],
    "avoidedFamilyIds": []
  },
  "constraints": {
    "excludedExerciseIds": [],
    "excludedFamilyIds": []
  }
}
```

Use opaque IDs. Do not require PII or medical diagnoses.

## Goals

Start with a small controlled vocabulary such as:

```text
hypertrophy
strength
muscular_endurance
general_fitness
skill_practice
power
```

Goal is context for explicit policies, not a hidden behavior switch.

## Preferences vs exclusions

Define:

```text
preferred = soft positive
avoided   = soft negative
excluded  = hard constraint
```

Support exercise and family IDs.

## TARGET evolution

TARGET remains "what the training should accomplish."

TrainingProfile remains "what the user/environment permits or prefers."

TARGET may expand to include:

- muscle volume
- muscle frequency
- movement-pattern coverage
- family coverage

Do not stuff environment constraints into TARGET.

## Plan evaluator API

```python
evaluate_plan(plan, db, profile=None, target=None, relationships=None)
```

Return structured sections such as:

```text
summary
muscleCoverage
frequency
movementPatterns
families
equipment
availability
preferences
constraints
warnings
errors
provenance
```

Hard constraints, soft preferences, and targets must remain separate.

Do not create a default 0–100 plan quality score.

## Duration estimation

Optional, explicit policy such as:

```text
duration-estimation-v1
```

Use transparent assumptions based on set count, rest, and transition overhead. If data is insufficient, return unknown.

## Plan assignment

Before adding a `plan-assignment.schema.json`, write an ADR deciding whether existing longitudinal plan activation already covers the required trainer/client semantics.

Applications own messaging, approval UI, and account relationships.

## v1.6 CLI

```bash
fedbpp evaluate-plan plan.json --db db.json --profile profile.json --target target.json
```

## v1.6 golden fixture

Create a hand-calculated fixture containing:

- muscle-volume gap
- frequency gap
- movement-pattern gap
- unavailable equipment
- excluded exercise
- soft preference warning
- known hard-constraint count

## v1.6 release gate

Release only when:

- TrainingProfile semantics stable
- deterministic evaluator implemented
- hard/soft/target categories distinct
- equipment, exclusions, frequency, patterns, families evaluated
- provenance complete
- CLI and installed wheel work
- all prior tests green

# 6. v1.7 — Training State + Progression Policies

## Objective

Derive a normalized current `TrainingState` from longitudinal history and use versioned progression policies to emit explicit Coach Decisions.

## TrainingState

Derived object, not manually authored.

Potential sections:

```text
subjectId
asOf
exerciseState
familyState
muscleState
adherenceState
planState
historyWindow
provenance
```

## ExerciseState

Per exercise:

```text
lastPerformed
recentSessionCount
recentSetCount
recentReps
recentLoads
recentRPE
recentRIR
lastPrescription
lastActual
adherence
```

Do not invent trends when data is sparse.

## MuscleState

Over an explicit history window:

```text
direct sets
indirect sets
effective sets
exposure frequency
target state
plan adherence
```

Support explicit windows such as last cycle, last 7 days, last 28 days, current phase.

## AdherenceState

Track session adherence, prescription adherence, repeated skipped exercises, repeated unplanned work, substitution frequency, and target under/overrun.

Do not infer motivation.

## Progression policy framework

Conceptual API:

```python
apply_progression_policy(policy, prescription, recent_actuals, training_state)
```

Initial policies:

```text
fixed
double_progression
rep_progression
load_progression
hold
```

Keep policies small and versioned.

## Double progression

Example:

```text
3 x 8–10 @ RIR 2
```

If all working sets hit the top rep target and effort remains within policy bounds, increase load; otherwise hold load and continue rep progression.

Rules must be explicit.

## CoachDecision

Likely portable artifact:

```text
coach-decision.schema.json
```

Example:

```json
{
  "decisionType": "increase_load",
  "exerciseId": "...",
  "policyId": "double-progression-v1",
  "before": {"load": {"value": 100, "unit": "kg"}},
  "after": {"load": {"value": 102.5, "unit": "kg"}},
  "reasonCodes": ["REP_TARGET_ACHIEVED", "RIR_WITHIN_TARGET"]
}
```

## Reason codes

Potential vocabulary:

```text
REP_TARGET_ACHIEVED
REP_TARGET_NOT_ACHIEVED
EFFORT_TOO_HIGH
EFFORT_TOO_LOW
LOAD_PROGRESS_STALLED
SET_TARGET_ACHIEVED
MISSED_PRESCRIPTION
REPEATED_SUBSTITUTION
INSUFFICIENT_DATA
POLICY_HOLD
```

## Decision types

Start with:

```text
increase_load
decrease_load
increase_reps
decrease_reps
increase_sets
decrease_sets
hold
```

Exercise replacement can wait.

## Explainability requirement

Every automated decision must include:

- policy ID/version
- input facts
- reason codes
- before
- after
- provenance

No unexplained plan mutation.

## v1.7 CLI

```bash
fedbpp training-state history.json --db db.json
fedbpp progress --plan plan.json --history history.json --policy double-progression-v1
```

## v1.7 release gate

TrainingState deterministic, at least one production progression policy implemented, CoachDecision explainable, CLI/wheel work, and all legacy tests green.

# 7. v1.8 — Deterministic Plan Generation

## Objective

Generate candidate PLANs from:

```text
TrainingProfile
+
TARGET
+
TrainingState
+
Exercise DB
+
Relationships
+
PlanningPolicy
```

The v1.6 evaluator is mandatory as the quality gate.

## Generation pipeline

```text
Profile + Target + State + DB + Policy
                  |
                  v
          candidate exercise pool
                  |
                  v
          candidate session structure
                  |
                  v
        volume/frequency allocation
                  |
                  v
            candidate PLAN
                  |
                  v
           evaluate_plan()
                  |
                  v
          accept / improve / reject
```

Do not permit direct LLM-to-canonical-PLAN generation without deterministic validation.

## PlanningPolicy

Versioned policy controls:

- split strategy
- candidate selection
- family diversity
- volume allocation
- frequency allocation
- set/repetition defaults
- effort targets
- duration assumptions
- progression-policy references

## Initial reference policies

Possible:

```text
full_body_general_v1
upper_lower_general_v1
push_pull_legs_general_v1
```

Goal-focused variants may follow, but do not call them universally optimal.

## PlanGenerationRequest

Potential inputs:

```text
profile
target
trainingState
policyId
locked exercises
required exercises
excluded exercises
```

Trainer and self-coached flows use the same request.

## Candidate selection

Use:

- available equipment
- exclusions
- preferences
- recent history
- families
- movement patterns
- target muscles
- continuity with existing plan

Return rationale. No hidden similarity score.

## Continuity and variation

Policies may prefer continuity or allow same-family variation. Do not implement default forced rotation.

## Volume allocation

Allocate toward TARGET using authoritative direct/indirect credits, respecting multi-muscle contributions.

## Frequency allocation

Honor muscle exposure targets, not only aggregate set totals.

## Session constraints

Respect session count, time, equipment, day availability, exercise/family exclusions.

If no valid plan exists, return:

```text
unsatisfiable
```

with exact reasons.

## GeneratedPlanResult

Return:

```text
plan
evaluation
policy
warnings
unsatisfiedSoftPreferences
provenance
```

## Determinism

Same DB/profile/target/state/policy/config must produce the same PLAN.

If randomness is ever allowed, require explicit seed and record it. Default is deterministic.

## Selection reason codes

Potential:

```text
TARGET_COVERAGE
EQUIPMENT_AVAILABLE
HISTORY_CONTINUITY
PREFERRED_EXERCISE
FAMILY_VARIATION
PATTERN_REQUIREMENT
```

## Trainer flow

```text
generate draft
-> trainer edits
-> evaluate edited PLAN
-> assign
```

## Self-trained flow

Same engine:

```text
profile + target + history
-> draft
-> user reviews
-> PLAN
```

## Current-plan comparison

Optionally report exercises added/removed, family changes, volume/frequency changes, and target-coverage changes.

## v1.8 golden tests

At minimum:

- 3-day full body
- 4-day upper/lower
- unavailable equipment
- excluded exercise
- excluded family
- preference honored
- impossible target
- family variation
- continuity from history
- deterministic regeneration

## v1.8 release gate

Valid deterministic PLAN generation, evaluator integration, explicit unsatisfiable results, shared trainer/self-coach engine, provenance/reasons, CLI/wheel, no adaptive auto-revision yet.

# 8. v1.9 — Adaptive Coaching / Plan Revision Engine

## Objective

Close the loop:

```text
PLAN
-> ACTUAL
-> longitudinal analysis
-> TrainingState
-> CoachDecision
-> PlanRevisionProposal
-> evaluate_plan()
-> new PLAN revision
```

## AdaptationPolicy

Versioned policy may control:

```text
progression
volume change
exercise continuity
exercise replacement
deload triggers
target-gap response
adherence response
session-count adaptation
```

Prefer composable sub-policies over one opaque coach policy.

## PlanRevisionProposal

Potential artifact:

```text
base plan/revision
proposed revision
CoachDecisions
evaluation before
evaluation after
reason codes
policy versions
provenance
```

Supports trainer approval.

## Trainer-assisted adaptive mode

System proposes revision; trainer reviews/edits/assigns.

## Automated mode

Application may auto-accept. DB++ only produces the proposal; product decides approval policy.

## Adaptation triggers

Potential deterministic triggers:

```text
progression achieved
repeated prescription failure
repeated substitution
persistent target underfill
persistent target overshoot
session-duration violation
equipment change
availability change
```

Be conservative with fatigue/recovery claims unless evidence-backed models exist.

## Persistent-condition logic

Policies may require N occurrences, consecutive periods, or rolling windows.

Example:

```text
if exercise skipped 3 consecutive occurrences:
    COACH_REVIEW_REQUIRED
```

Not every signal should cause automatic replacement.

## Exercise replacement

If policy permits, candidate pool may use same family, compatible equipment, movement patterns, coverage difference, history, and preferences.

Same family != automatic replacement or physiological equivalence.

## Volume adaptation

Critically distinguish:

```text
plan insufficient
vs
plan not followed
```

Example:

```text
PLAN 8 / ACTUAL 8 / TARGET 10–14
=> plan may need more volume

PLAN 12 / ACTUAL 7 / TARGET 10–14
=> adherence issue, not automatically increase prescription
```

This distinction must be explicit.

## Automated-coach explanations

DB++ returns facts and reason codes; UI/LLM turns them into prose.

Example:

```json
{
  "decisionType": "increase_sets",
  "reasonCodes": [
    "TARGET_BELOW_MINIMUM",
    "HIGH_PLAN_ADHERENCE",
    "CURRENT_VOLUME_BELOW_TARGET"
  ]
}
```

# 9. LLM boundary

Recommended:

```text
Natural-language user intent
        |
        v
       LLM
        |
        v
TrainingProfile / TARGET / constraints
        |
        v
DB++ deterministic engine
        |
        v
PLAN / Evaluation / CoachDecision
        |
        v
       LLM
        |
        v
human-readable explanation
```

LLM handles language.

DB++ handles calculations and policy decisions.

Core operation must not require an LLM.

# 10. Common policy architecture

Potential policy families:

```text
analysis policy
duration policy
progression policy
planning policy
adaptation policy
```

Each should have:

```text
policyId
policyVersion
parameters
description
```

Avoid hidden behavior.

A policy change that can alter generated plans or decisions requires a new policy version. Never silently mutate an existing policy ID.

Policies must not silently depend on current time, randomness, remote services, identity, or mutable global config.

# 11. Constraint priority

Recommended planning priority:

```text
1 validity
2 hard constraints
3 target minimums
4 target targets
5 soft preferences
6 tie-breaking / optimization
```

Version this within planning policy.

Do not create a single default "plan quality score."

# 12. Explainability as a release gate

Every generated or adaptive choice must be able to answer:

> Why was this chosen or changed?

If structured reasons are unavailable, the feature is not ready.

# 13. No hidden AI

No embeddings, remote recommendation APIs, or LLM calls in core planning.

Application layers may use AI to translate natural language into structured inputs or structured outputs into prose.

# 14. Evidence boundary

Reference policies should state whether they are:

```text
general reference
research-derived
coach-defined
user-defined
```

Do not call a policy scientifically optimal unless evidence supports the exact claim.

# 15. Trainer/app boundary

DB++ owns:

```text
evaluate PLAN
analyze ACTUAL
derive TrainingState
suggest progression
generate draft PLAN
propose PLAN revision
```

Application owns:

```text
accounts
trainer-client invitations
messaging
notifications
approval UI
billing
permissions
sync
```

# 16. Self-trained and automated-coach modes

Self-trained users use the same Profile/TARGET/Evaluator/State/Generator/Decision APIs.

Automated coaching is the same deterministic engine plus an application decision to auto-accept proposals.

No special core "AI coach" mode is needed.

# 17. Research value

Researchers should be able to reproduce:

```text
profile
target
history
policy versions
generated PLAN
CoachDecisions
resulting ACTUAL
```

Future research tables may include policy ID, decision type, before/after, reason codes, and revision IDs.

# 18. Cross-language strategy

Python remains the reference implementation.

Swift/Kotlin prioritize schema/model compatibility and app-facing data types.

R remains research-focused.

Do not block reference releases on complete cross-language parity, but never claim parity that does not exist.

# 19. CLI roadmap

```text
v1.6  fedbpp evaluate-plan
v1.7  fedbpp training-state
      fedbpp progress
v1.8  fedbpp generate-plan
v1.9  fedbpp propose-revision
```

CLI should remain thin over public APIs.

# 20. Schema strategy

Potential future schemas:

```text
training-profile.schema.json
coach-decision.schema.json
plan-generation-request.schema.json
plan-revision-proposal.schema.json
```

Only create schemas for genuine portable domain artifacts.

# 21. Compatibility

Do not break:

```text
exerciseId
PLAN
ACTUAL
TARGET existing semantics
relationship artifact
interop mappings
longitudinal semantics
```

New functionality should be additive.

# 22. Testing philosophy

Every major policy must have hand-calculated fixtures asserting:

```text
inputs
decision
reason codes
resulting plan
evaluation
```

Avoid snapshot-only testing.

# 23. v1.6 tests

Required categories:

```text
TrainingProfile validation
goals
availability
equipment
hard exclusions
soft preferences
target gaps
frequency gaps
movement-pattern gaps
family gaps
duration estimation
PlanEvaluation provenance
CLI
installed wheel
```

# 24. v1.7 tests

```text
TrainingState derivation
history windows
exercise state
muscle state
adherence state
double progression
load increment
hold
insufficient data
CoachDecision reason codes
determinism
```

# 25. v1.8 tests

```text
candidate pool
equipment filtering
exclusions
preferences
family continuity
target allocation
frequency
movement constraints
unsatisfiable request
deterministic generation
evaluator integration
```

# 26. v1.9 tests

```text
adaptation trigger
progression
persistent target gap
adherence failure
unplanned work
plan insufficiency vs nonadherence
revision proposal
trainer-review mode
automatic-mode output equivalence
reason codes
provenance
```

# 27. CI

Retain every prior test.

Add dedicated stages as each new layer lands.

Installed-wheel and CLI smoke tests remain mandatory.

# 28. Release strategy

```text
v1.6.0  TrainingProfile + PlanEvaluation
v1.6.x  evaluator corrections

v1.7.0  TrainingState + progression

v1.8.0  deterministic plan generation

v1.9.0  adaptive coaching
```

Do not rush v2.0.

# 29. v2.0 decision point

After v1.9, reassess highest-value direction based on adoption.

Possible directions:

- advanced anatomy
- richer evidence-backed policies
- more interoperability
- research standardization
- broader platform parity

Fine anatomy is not automatically the next feature.

# 30. Documentation

Add as needed:

```text
docs/TRAINING-PROFILE.md
docs/PLAN-EVALUATION.md
docs/TRAINING-STATE.md
docs/PROGRESSION-POLICIES.md
docs/PLAN-GENERATION.md
docs/ADAPTIVE-COACHING.md
docs/COACH-DECISIONS.md
```

Recommended ADRs:

```text
training-profile-vs-target
hard-vs-soft-constraints
plan-evaluation-semantics
policy-versioning
training-state-windowing
coach-decision-explainability
plan-generation-determinism
adaptive-plan-revision
LLM-boundary
```

# 31. Immediate next action

Begin v1.6:

1. audit current TARGET/profile-related needs;
2. write ADR separating TrainingProfile from TARGET;
3. design `training-profile.schema.json`;
4. extend TARGET only where justified;
5. implement deterministic `evaluate_plan()`;
6. expose hard/soft/target result categories;
7. add golden evaluator fixtures;
8. expose Python API and CLI;
9. run every legacy test;
10. release v1.6.0.

Do not begin plan generation until evaluator semantics are stable.

# 32. Overall definition of success

The application layer should eventually delegate:

```text
create profile
evaluate plan
assign plan
receive actuals
analyze adherence
derive training state
suggest progression
generate draft plan
propose revision
```

to DB++.

Trainer, self-trained, and automated-coach products should all use the same domain semantics.

The engine must remain:

```text
deterministic
portable
explainable
versioned
testable
privacy-neutral
UI-independent
```

That is the intended long-term identity of Free Exercise DB++.
