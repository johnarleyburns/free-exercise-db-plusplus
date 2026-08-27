# Free Exercise DB++ Roadmap

Status: **v1.11.0 release prepared**
Current stable release: **v1.11.0**
Primary direction: **portable workout-intent, planning, and adaptive-coaching engine with first-class Python and Swift packages**

---

# 1. Product vision

Free Exercise DB++ has evolved from an exercise-definition database into a deterministic training-domain engine.

Through v1.9 it now provides:

- stable exercise identity;
- normalized movement and muscle semantics;
- direct / indirect / stabilizer analysis;
- PLAN / ACTUAL / TARGET interchange;
- longitudinal analysis;
- exercise families and relationships;
- TrainingProfile;
- PlanEvaluation;
- TrainingState;
- progression policies;
- deterministic plan generation;
- adaptive coaching proposals;
- research exports;
- external interoperability mappings.

The next objective is to make the same deterministic training semantics easily usable from multiple environments:

```text
Swift / Apple apps
Kotlin / Android apps
Python / services, notebooks, automation
R / research and statistical workflows
```

## v1.11 COMPLETE (2026-08-27)

The Python reference engine is audited and complete, and the Swift native
engine matches the released Python semantics for intent resolution, TARGET and
profile handling, plan analysis/evaluation, history and adherence-rich state,
progression, deterministic production generation, and adaptive coaching.
Canonical fixtures, resource copies, isolated consumers, and deterministic
native results are covered by the parity suite.

v1.12 NEXT: Swift SPM production hardening: API ergonomics, documentation,
distribution, resource-size/performance work, app-integration examples,
semantic stability, and drop-in application readiness. It owns no missing core
engine semantics. DB++ remains free of LLM vendor dependencies.

v1.13: Kotlin/JVM/Android full engine port.

v1.14: R research/full analysis port.

The completed v1.11 workflow is:

```text
structured WorkoutIntent
        |
        v
resolveIntent()
        |
        +--> TrainingProfile
        +--> TARGET
        +--> planning policy
        +--> generation constraints
        |
        v
generatePlan()
        |
        v
evaluatePlan()
        |
        v
WorkoutPlan
```

With existing history:

```text
WorkoutIntent
        +
current PLAN
        +
ACTUAL history
        |
        v
TrainingState
        |
        v
adaptPlan()
        |
        +--> CoachDecision[]
        +--> proposed PLAN revision
        +--> current/proposed evaluation
```

The same conceptual workflow must be available through first-class language packages.

---

# 2. Application / engine boundary

Free Exercise DB++ owns:

```text
exercise vocabulary
exercise relationships
PLAN / ACTUAL / TARGET
TrainingProfile
WorkoutIntent
intent resolution
goal resolution
environment/equipment profiles
plan evaluation
TrainingState
progression
plan generation
adaptive coaching
CoachDecision
policy versioning
provenance
research/interchange semantics
```

Consuming applications own:

```text
LLM integration
prompting
conversation state
voice UI
Apple Foundation Models
cloud-hosted models
UI
accounts
trainer/client relationships
authorization
persistence
sync
messaging
notifications
billing
approval/activation workflow
```

The core packages must not depend on a particular LLM framework.

---

# 3. Cross-language support is a first-class requirement

The project maintains four primary package surfaces:

```text
packages/python
packages/swift/FreeExerciseDBPlusPlus
packages/kotlin
packages/r
```

The languages have different product roles, but all must consume the same public artifacts and preserve the same core semantics.

## Python

Role:

- reference implementation;
- full semantic oracle;
- CLI;
- service/backend usage;
- notebooks;
- automated validation;
- research preprocessing.

## Swift

Role:

- native iOS/macOS application integration;
- offline/on-device planning and coaching;
- primary package for Apple application usage;
- Foundation-only core where practical;
- no FoundationModels dependency.

## Kotlin

Role:

- Android/JVM application integration;
- offline/native planning and coaching;
- server/JVM consumers where useful.

## R

Role:

- research;
- statistical workflows;
- tidy data;
- experiment analysis;
- reproducibility;
- participant/cohort analysis.

R does not need to duplicate every interactive app convenience API, but it must understand the same interchange artifacts and reproduce the same canonical analyses where relevant.

---

# 4. Parity philosophy

Cross-language parity does **not** mean every package must contain identical code.

It means:

```text
same input artifact
same policy version
same DB version
same semantic operation
        ↓
same canonical result
```

for operations claimed as supported in that language.

Capabilities must be explicitly documented.

Never claim parity where it does not exist.

---

# 5. Shared semantic source of truth

Public semantics live in:

```text
schemas
versioned JSON artifacts
ADRs
normative docs
shared golden fixtures
```

Python remains the reference implementation, and Swift is checked against the
same common golden fixtures rather than independently evolving behavior.

---

# 6. Stable foundation through v1.9

Treat the following as stable unless a real defect requires correction.

## v1.0

Exercise vocabulary and evidence-audited muscle/movement semantics.

## v1.1

PLAN / ACTUAL / TARGET, ranges, arbitrary cycles, periodization, PLAN analysis, PLAN-vs-ACTUAL, adherence.

## v1.2

Interoperability mappings and loss/provenance model.

## v1.3

Operational conversion, FHIR, CLI.

## v1.4.1

Longitudinal analysis, revision activation, repeated occurrence matching, research exports.

## v1.5.1

Exercise families/relationships and family-level analysis.

## v1.6

TrainingProfile + deterministic PlanEvaluation.

## v1.7.1

TrainingState + progression + CoachDecision.

## v1.8

Deterministic plan generation.

## v1.9

Adaptive coaching / PLAN revision proposal engine.

---

# 7. Release sequence to the app/research goal

```text
v1.10  WorkoutIntent + deterministic intent/goal/environment resolution

v1.11  COMPLETE: Python reference audit and full Swift engine parity

v1.12  NEXT: Swift SPM production hardening and app-readiness polish

v1.13  Kotlin/JVM/Android full engine port

v1.14  R research/full analysis port
```

---

# 8. Acceptance scenario

The roadmap is successful when a consuming app or tool can represent:

```text
"I want to work out 5 times a week,
 Monday through Thursday and Saturday.
 I can do 3–4 exercises per workout.
 I have a regular commercial gym.
 My goal is hypertrophy."
```

as:

```text
WorkoutIntent
  goal = hypertrophy
  cycleLengthDays = 7
  sessionsPerCycle = 5
  preferredWeekdays = Mon/Tue/Wed/Thu/Sat
  exercisesPerSession = 3–4
  environment = commercial_gym
```

and then call the domain package.

The LLM-to-WorkoutIntent mapping is outside the repo.

---

# 9. v1.10 — WorkoutIntent + deterministic resolution (complete)

## Objective

Create a portable representation of a training request and a deterministic resolver that converts it into the existing DB++ planning inputs.

The resolver must bridge:

```text
human/app request
→ WorkoutIntent
→ TrainingProfile/TARGET/policy/options
```

without using an LLM internally.

---

# 10. WorkoutIntent concept

WorkoutIntent represents the current request.

It is not a replacement for TrainingProfile.

Examples:

```text
train five days this cycle
train Monday through Thursday and Saturday
keep sessions to 3–4 exercises
focus on hypertrophy
keep bench press
change as little as possible
commercial gym
home dumbbells only
```

TrainingProfile remains reusable subject/environment context.

---

# 11. WorkoutIntent vs TARGET

High-level:

```text
goal = hypertrophy
```

belongs in WorkoutIntent.

Concrete:

```text
chest effective sets target 12
```

belongs in TARGET.

Intent resolution uses a versioned goal policy to produce default TARGET values.

Explicit user TARGET input overrides defaults.

---

# 12. WorkoutIntent schema

Create:

```text
workout-intent.schema.json
```

Initial independent schemaVersion:

```text
0.1.0
```

Likely fields:

```text
schemaVersion
intentId
subjectId optional
goal
schedule
sessionConstraints
environment
equipmentOverrides
exerciseConstraints
preferences
continuity
useHistory
requestedPolicy optional
```

No PII required.

---

# 13. Schedule semantics

Support:

```text
cycleLengthDays
sessionsPerCycle
preferredDayOffsets
excludedDayOffsets
preferredWeekdays
excludedWeekdays
```

Weekday syntax exists for natural user requests.

PLAN remains cycle-relative.

---

# 14. Weekday resolution

For 7-day cycles, deterministic mapping from weekday to dayOffset requires an explicit anchor or a canonical Monday-based cycle convention.

Choose one and document it.

Recommended:

```text
7-day intent weekday mode:
Monday = dayOffset 0
Tuesday = 1
...
Sunday = 6
```

This makes intent independent of actual calendar date.

For non-7-day cycles:

weekday fields should normally be invalid unless an explicit calendar anchor is provided.

Do not guess.

---

# 15. Exercises-per-session

Add first-class support for:

```text
minExercisesPerSession
targetExercisesPerSession
maxExercisesPerSession
```

This is required for the target app scenario.

Recommended semantics:

```text
minimum / maximum = hard
target = soft
```

PlanEvaluation must check it.

Plan generation must satisfy it.

---

# 16. Training environments

Introduce versioned environment presets.

Initial:

```text
commercial_gym
home_gym
minimal_equipment
bodyweight_only
custom
```

Environment resolves to explicit normalized equipment.

---

# 17. Commercial gym reference profile

Create:

```text
commercial-gym-general-v1
```

using actual DB++ equipment vocabulary.

This is a convenience default, not a guarantee every commercial gym has all equipment.

Users can override equipment.

---

# 18. Equipment overrides

Support:

```text
availableEquipment
unavailableEquipment
```

or equivalent additive/subtractive semantics.

Resolved output contains explicit equipment.

Downstream generator should not need to understand `commercial_gym`.

---

# 19. Exercise constraints

Support intent-level:

```text
requiredExerciseIds
lockedExerciseIds
excludedExerciseIds
preferredExerciseIds
avoidedExerciseIds

requiredFamilyIds
excludedFamilyIds
preferredFamilyIds
avoidedFamilyIds
```

These are merged with TrainingProfile using deterministic precedence.

---

# 20. Continuity

Support structured:

```text
preserve
neutral
vary
```

plus explicit locked exercise IDs.

No natural-language parsing in core.

---

# 21. Use-history flag

Support explicit:

```text
useHistory
```

and optionally a requested state window.

If history is absent, generation remains valid.

If history is supplied and enabled, derive TrainingState canonically.

---

# 22. Missing-information result

Create:

```text
IntentResolutionResult
```

with:

```text
status
resolvedProfile
resolvedTarget
planningPolicy
generationOptions
missingInformation
warnings
provenance
```

Statuses:

```text
resolved
resolved_with_defaults
needs_clarification
invalid
unsatisfiable
```

This is essential for LLM-facing apps.

---

# 23. Structured clarification needs

Return machine-readable missing facts:

```json
{
  "field": "goal",
  "reason": "required_for_goal_policy_resolution"
}
```

The consuming LLM/UI asks the question.

DB++ does not write conversational text.

---

# 24. Goal policies

Introduce versioned reference goal resolution policies.

Required:

```text
general-hypertrophy-v1
general-strength-v1
```

Later:

```text
general-muscular-endurance-v1
general-fitness-v1
```

Goal policy may output:

```text
default TARGET
planning policy
default rep prescription policy
default effort policy
```

All choices must be documented.

---

# 25. Hypertrophy policy

`general-hypertrophy-v1` must be explicit, versioned, and conservative.

It may provide default:

```text
muscle set targets
frequency targets
rep ranges
effort targets
```

only where methodology is documented.

Do not call the result optimal.

Explicit user/trainer targets override it.

---

# 26. Precedence

Document and test precedence.

Recommended conceptual order:

```text
explicit request hard constraints
explicit TARGET values
explicit TrainingProfile constraints
explicit WorkoutIntent soft preferences
versioned goal/environment defaults
```

Hard conflicts must return invalid/unsatisfiable.

Do not silently pick one.

---

# 27. Intent resolver API

Python reference:

```python
resolved = resolve_intent(
    intent,
    db,
    profile=None,
    target=None,
    relationships=None,
    history=None,
)
```

Resolution does not itself generate a plan.

---

# 28. Intent-to-plan convenience API

May expose:

```python
generate_plan_from_intent(...)
```

but internally it must remain:

```text
resolve_intent
→ derive TrainingState if required
→ generate_plan
→ evaluate_plan
```

and expose intermediate structured results.

---

# 29. Intent and adaptation

For existing active PLAN:

```text
resolve intent
→ merge updated constraints/profile/target
→ adapt_plan()
```

Application decides whether it wants a new plan or adaptation.

No hidden auto-detection.

---

# 30. Provenance

Intent resolution records:

```text
intentSchemaVersion
goalPolicyId/version
environmentPolicyId/version
defaultsApplied
explicitOverrides
profile version
TARGET version
DB version
relationship version
```

---

# 31. v1.10 golden scenario

Required exact fixture:

```text
goal = hypertrophy
cycle = 7
sessions = 5
weekdays = Mon Tue Wed Thu Sat
exercises/session = 3–4
environment = commercial gym
```

Assert:

```text
resolved status
five allowed/preferred session days
3–4 exercise hard range
explicit equipment set
goal policy
resolved TARGET
planning policy
deterministic output
generated PLAN passes evaluate_plan
```

---

# 32. v1.10 clarification tests

At minimum:

```text
empty intent
goal only
schedule only
environment only
conflicting days
required+excluded same exercise
custom equipment without environment
non-7-day cycle with weekday request
```

---

# 33. v1.10 PlanEvaluation changes

PlanEvaluation must evaluate:

```text
exercise count per session
resolved day constraints
equipment constraints
```

Generator and resolver may not become separate sources of truth.

---

# 34. v1.10 CLI

Add:

```text
fedbpp resolve-intent
fedbpp generate-from-intent
```

CLI takes JSON intent, not natural language.

---

# 35. v1.10 docs

Create:

```text
docs/WORKOUT-INTENT.md
docs/GOAL-RESOLUTION.md
docs/ENVIRONMENT-PROFILES.md
```

ADRs:

```text
WorkoutIntent vs TrainingProfile vs TARGET
intent precedence
weekday semantics
exercise-count constraints
goal-policy semantics
environment profile semantics
```

---

# 36. v1.10 cross-language preparation

Before v1.10 release, define language-neutral fixtures for all new intent semantics.

Store under something like:

```text
fixtures/cross-language/intent/
```

These become the parity oracle for v1.11/v1.12.

---

# 37. v1.10 release gate

v1.10 complete only when:

- WorkoutIntent schema stable enough for consumers;
- deterministic intent resolution works;
- hypertrophy/strength policies exist;
- commercial-gym environment works;
- weekday resolution works;
- 3–4 exercise/session constraint is real;
- missing information is structured;
- history-free and history-aware generation work;
- Python reference API/CLI green;
- cross-language fixtures published;
- no LLM dependency exists.

---

# 38. v1.11 — Cross-language semantic parity

## Objective

Bring Swift, Kotlin, and R forward against the v1.10 reference semantics while preserving Python as the semantic oracle.

The major focus is not API cosmetics.

It is semantic parity.

---

# 39. Shared fixture architecture

Create canonical fixtures covering:

```text
schema decoding
WorkoutIntent
intent resolution
TrainingProfile
TARGET
PlanEvaluation
plan generation
TrainingState
CoachDecision
adaptive coaching where language claims support
```

Suggested:

```text
fixtures/cross-language/
  intent/
  evaluation/
  planning/
  history/
  coaching/
```

Each fixture contains:

```text
inputs/
expected/
metadata.json
```

Expected results generated by the versioned Python reference and committed for review.

---

# 40. Canonical serialization

Define canonical JSON comparison rules.

At minimum:

```text
stable field ordering where serialized for fixtures
stable list ordering
floating point tolerance policy
date/time normalization
unit representation
null/missing semantics
```

Avoid comparing implementation-specific object descriptions.

---

# 41. Capability matrix

Create:

```text
docs/LANGUAGE-CAPABILITIES.md
```

Matrix rows:

```text
load DB
load relationships
PLAN decode
ACTUAL decode
TARGET decode
WorkoutIntent
resolveIntent
evaluatePlan
TrainingHistory
deriveTrainingState
progression
generatePlan
adaptPlan
research exports
FHIR conversion
```

Columns:

```text
Python
Swift
Kotlin
R
```

Use:

```text
full
read-only
partial
not-supported
```

Never hide gaps.

---

# 42. Python v1.11 role

Python remains full-reference implementation.

Required:

```text
all v1.10 functionality
all prior analysis/planning/coaching
CLI
fixture generator/validator
```

Add helpers to emit canonical fixture expected output.

---

# 43. Swift v1.11 objective

Upgrade existing:

```text
packages/swift/FreeExerciseDBPlusPlus
```

from a read-only PLAN/ACTUAL consumer into a native training-domain package.

Current package already exists and currently provides Foundation-only Codable
models and coverage analysis.

v1.11 must add native intent/planning functionality rather than wrapping Python.

---

# 44. Swift package constraints

Swift package should remain:

```text
Swift 6
Foundation-only core
Sendable-safe where practical
no SwiftUI requirement
no FoundationModels dependency
no CloudKit dependency
no persistence framework dependency
no network requirement
```

---

# 45. Swift SPM installation

The consumer should be able to:

```swift
import FreeExerciseDBPlusPlus
```

after adding the package through Swift Package Manager.

No manual copying of DB JSON or relationship JSON should be required for bundled/default operation by v1.12.

---

# 46. Swift typed models

Provide public typed models for:

```text
Exercise
ExerciseDatabase
ExerciseRelationshipRegistry
WorkoutPlan
WorkoutActual
VolumeTarget
TrainingProfile
WorkoutIntent
IntentResolutionResult
PlanEvaluation
TrainingHistory
TrainingState
CoachDecision
GeneratedPlanResult
AdaptivePlanResult
```

Avoid public `[String: Any]`.

---

# 47. Swift controlled vocabularies

Use typed enums or forward-compatible wrappers for:

```text
TrainingGoal
Weekday
TrainingEnvironment
Equipment
MovementPattern
IntentResolutionStatus
GenerationStatus
AdaptiveStatus
CoachDecisionType
ReasonCode
```

Define unknown-value handling deliberately.

---

# 48. Swift partial ranges

Implement one consistent model preserving:

```text
minimum
target
maximum
```

independently.

Do not use a range type that loses partial bounds.

---

# 49. Swift database resources

Bundle canonical resources or generate equivalent typed resources so a caller can do:

```swift
let engine = try TrainingEngine.bundled()
```

Custom resource injection must remain possible.

---

# 50. Swift engine facade

Target public API:

```swift
public struct TrainingEngine {
    public func resolveIntent(...)
    public func evaluatePlan(...)
    public func generatePlan(...)
    public func deriveTrainingState(...)
}
```

By v1.12:

```swift
public func adaptPlan(...)
```

must also be available.

---

# 51. Swift parity tests

For every supported operation:

```text
load shared fixture
run Swift implementation
canonicalize output
compare to committed Python reference output
```

No independently invented Swift expected semantics.

---

# 52. Kotlin v1.11 objective

Upgrade Kotlin package into a first-class native/JVM domain consumer.

Support Android/JVM usage without Python.

Primary target:

```text
WorkoutIntent
intent resolution
PlanEvaluation
plan generation
TrainingState
```

Adaptive coaching parity may complete in v1.12.

---

# 53. Kotlin packaging

Use standard Gradle/JVM/Kotlin packaging.

Keep Android framework dependencies out of core where practical.

Core package should work in plain JVM tests.

---

# 54. Kotlin typed models

Provide idiomatic:

```text
data classes
sealed classes/enums
serialization support
```

for the same portable artifacts.

Avoid raw dynamic maps as the primary API.

---

# 55. Kotlin resource strategy

Provide convenient bundled/default DB access for Android/JVM while allowing caller-supplied resources.

Do not require network access.

---

# 56. Kotlin parity fixtures

Run the exact shared fixture corpus used by Python/Swift.

Document any unsupported operations in the capability matrix.

---

# 57. R v1.11 objective

Strengthen the R package around research use.

R priorities:

```text
schema/artifact readers
WorkoutIntent parsing
resolved input inspection
PlanEvaluation
TrainingHistory analysis
TrainingState
cohort/research tables
generated PLAN inspection
CoachDecision/adaptation result inspection
```

R need not necessarily implement the full plan search engine in native R by v1.11 if that is not valuable.

However, semantics it claims to support must be parity-tested.

---

# 58. R tidy interfaces

Provide functions returning data frames/tibbles for:

```text
intent summary
target summary
plan evaluation
muscle coverage
session coverage
training state
coach decisions
plan changes
```

Do not flatten away:

```text
missing vs zero
partial ranges
unmapped state
```

---

# 59. R reproducibility

Every research result should expose policy/version provenance.

Researchers must be able to save:

```text
DB version
intent
profile
TARGET
policy IDs
PLAN
ACTUAL
TrainingState
CoachDecision
```

---

# 60. Cross-language numeric semantics

Explicitly test:

```text
effective set calculations
custom set credits
range arithmetic
normalization to 7 days
unit conversions where supported
target deficit/excess
```

No language may hardcode default credits.

---

# 61. Cross-language date/time semantics

Test:

```text
timezone offsets
asOf
history windows
week boundary
non-7-day cycles
weekday intent resolution
```

---

# 62. Cross-language determinism

Swift/Kotlin/Python generation should produce semantically identical plans for shared reference policies.

If exact IDs differ because of language-specific serialization, fix the ID generation.

Do not accept "roughly the same plan" as parity.

---

# 63. v1.11 release gate

v1.11 complete when:

- shared parity fixtures exist;
- capability matrix exists;
- Python remains green reference;
- Swift resolves intent natively;
- Swift evaluates plans natively;
- Swift generates plans natively for reference policies;
- Kotlin resolves/evaluates/generates for declared policy set;
- R consumes intent/evaluation/state artifacts and reproduces declared analyses;
- package docs are accurate;
- parity CI is green.

---

# 64. v1.12 — Production-ready language packages

## Objective

Make the packages easy to consume from real applications and research workflows.

The flagship app deliverable is the Swift SPM, but Python, Kotlin, and R are also release-grade first-class packages.

---

# 65. v1.12 package goal

The four packages should be installable through normal language workflows:

```text
Swift Package Manager
Python pip/wheel
Gradle/Maven-style Kotlin/JVM package
R package install workflow
```

The exact publishing registry may vary, but installability and documentation are mandatory.

---

# 66. Swift v1.12 final capability

Swift must support end-to-end:

```text
WorkoutIntent
→ resolveIntent
→ generatePlan
→ evaluatePlan
```

and, with history:

```text
TrainingHistory
→ deriveTrainingState
→ adaptPlan
→ proposed PLAN + CoachDecision[]
```

All natively.

No Python runtime.

No subprocess.

No network service.

No LLM dependency.

---

# 67. Swift drop-in example

Target usage:

```swift
import FreeExerciseDBPlusPlus

let engine = try TrainingEngine.bundled()

let intent = WorkoutIntent(
    goal: .hypertrophy,
    schedule: .init(
        cycleLengthDays: 7,
        sessionsPerCycle: .exact(5),
        preferredWeekdays: [
            .monday,
            .tuesday,
            .wednesday,
            .thursday,
            .saturday
        ]
    ),
    sessionConstraints: .init(
        exercisesPerSession: .init(minimum: 3, maximum: 4)
    ),
    environment: .commercialGym
)

let resolved = try engine.resolveIntent(intent)

let result = try engine.generatePlan(
    resolvedIntent: resolved
)

guard let plan = result.plan else {
    // app/LLM inspects result.missingInformation / unsatisfied constraints
    return
}
```

---

# 68. Swift history-aware example

```swift
let state = try engine.deriveTrainingState(
    history: history,
    asOf: Date()
)

let proposal = try engine.adaptPlan(
    intent: intent,
    currentPlan: currentPlan,
    history: history,
    asOf: Date()
)
```

`Date()` is supplied by the application.

The package must not hide current-time dependence.

---

# 69. App/LLM integration contract

The package should expose structures that are easy for an LLM adapter to create/consume, but should not know about the LLM.

The application can map:

```text
LLM output
→ WorkoutIntent
```

and:

```text
IntentResolutionResult.missingInformation
→ clarification prompt
```

and:

```text
GeneratedPlanResult / CoachDecision
→ natural-language explanation
```

This is the whole intended integration boundary.

---

# 70. Swift error model

Provide typed errors for:

```text
invalidIntent
needsClarification
invalidProfile
invalidTarget
unsatisfiable
resourceLoadFailure
schemaMismatch
unsupportedPolicy
```

Avoid requiring callers to parse arbitrary strings.

---

# 71. Swift concurrency

Public value models should be `Sendable` where practical.

Engine should be safe to use from modern Swift concurrency patterns.

Avoid global mutable state.

---

# 72. Swift performance

Target normal mobile usage:

```text
load bundled DB once
reuse indexed engine
intent resolution near-instant
plan evaluation near-instant
plan generation responsive
adaptive analysis reasonable for normal user history
```

Pre-index exercise IDs/families/muscles.

No database dependency required.

---

# 73. Swift package resources/versioning

Expose:

```swift
engine.databaseVersion
engine.relationshipVersion
engine.supportedPolicyVersions
```

or equivalent provenance.

Consumers must be able to record exactly what engine produced a plan.

---

# 74. Kotlin v1.12 final capability

Kotlin should support end-to-end app usage for the declared core workflow:

```text
WorkoutIntent
resolveIntent
evaluatePlan
generatePlan
deriveTrainingState
adaptPlan
```

If any feature remains unsupported, capability docs must say so before release.

Goal is full parity with Swift/Python for training-domain operations by v1.12.

---

# 75. Kotlin Android usability

Provide README/example for:

```text
Android ViewModel/service usage
offline engine loading
bundled resources
structured plan generation
```

Do not couple the core library to Compose/UI.

---

# 76. Python v1.12 final capability

Python remains complete reference.

Provide polished APIs:

```text
resolve_intent
generate_plan_from_intent
evaluate_plan
derive_training_state
adapt_plan
```

Maintain CLI equivalents.

Wheel must include required default resources or provide a documented loader.

---

# 77. Python service usage

Document simple service/server pattern without making web frameworks dependencies.

Example:

```python
engine = TrainingEngine.bundled()
result = engine.generate_plan_from_intent(intent)
```

---

# 78. R v1.12 final capability

R package should be research-ready.

Required:

```text
read/validate WorkoutIntent
read PLAN / ACTUAL / TARGET
evaluate plan
derive longitudinal/research summaries
derive TrainingState or consume canonical TrainingState
inspect generated/adaptive plans
tidy CoachDecision/change outputs
cohort export
```

Native plan generation/adaptation in R is desirable if practical, but not required if the package clearly focuses on research consumption.

If not natively supported, do not fake parity.

---

# 79. R research example

Ship a reproducible example:

```text
100 subjects
WorkoutIntent/protocol
PLAN
12 weeks ACTUAL
TrainingState
adaptive decisions
subject-week-muscle table
```

Show loading into tidy R analysis.

Do not include inferential conclusions as core package behavior.

---

# 80. Package API naming

Aim for conceptually parallel names:

```text
resolveIntent / resolve_intent
evaluatePlan / evaluate_plan
generatePlan / generate_plan
deriveTrainingState / derive_training_state
adaptPlan / adapt_plan
```

Language idioms may differ.

Semantic operation names should remain recognizable.

---

# 81. Shared package documentation

Create:

```text
docs/PACKAGE-QUICKSTART.md
docs/LANGUAGE-CAPABILITIES.md
docs/CROSS-LANGUAGE-PARITY.md
```

Each package gets its own README.

---

# 82. Cross-language fixtures by v1.12

Mandatory fixture families:

```text
WorkoutIntent exact user scenario
missing-information clarification
commercial gym
custom equipment
3-day full body
5-day hypertrophy
non-7-day cycle
PlanEvaluation hard constraint
TrainingState window
double progression
explicit substitution
target deficit
adaptive revision
adaptive regeneration
custom set credits
```

---

# 83. Cross-language CI

CI should include independent stages:

```text
python
swift
kotlin
r
cross-language-fixtures
```

The parity stage compares normalized outputs.

A release cannot claim parity if the fixture suite is red.

---

# 84. Semantic version compatibility

Project release version and schema versions remain independent.

Language package versions should clearly identify compatible project releases.

Document:

```text
package version
supported DB schema versions
supported WorkoutIntent schema versions
supported PLAN/ACTUAL/TARGET versions
supported policy versions
```

---

# 85. Forward compatibility

Portable JSON decoders need a strategy for unknown future enum values.

Do not silently map unknown values to incorrect existing values.

Preferred:

```text
unknown(rawValue)
```

where language supports it, or explicit validation failure where required.

---

# 86. Offline-first requirement

All core domain operations required for:

```text
intent resolution
plan evaluation
plan generation
TrainingState
adaptive coaching
```

must work without network access.

This is especially important for mobile apps.

---

# 87. Privacy requirement

No language package requires:

```text
name
email
DOB
address
account ID
medical diagnosis
```

Opaque subject IDs remain sufficient.

---

# 88. No app-specific dependencies

Swift:

```text
no FoundationModels
no SwiftUI
no CloudKit
```

Kotlin:

```text
no Compose requirement
no Android framework requirement in core if avoidable
```

Python:

```text
no web framework dependency
```

R:

```text
no hosted service dependency
```

---

# 89. v1.12 final golden acceptance test

The exact cross-language fixture:

```text
Goal:
hypertrophy

Schedule:
5 sessions / 7-day cycle
Mon Tue Wed Thu Sat

Exercises/session:
3–4

Environment:
commercial gym
```

must resolve/generate deterministically.

Python, Swift, and Kotlin must produce semantically equivalent:

```text
resolved intent
TrainingProfile
TARGET
planning policy
PLAN
PlanEvaluation
```

R must at minimum load/validate the artifacts and reproduce the analysis outputs.

---

# 90. v1.12 history-aware golden test

Given:

```text
same WorkoutIntent
current PLAN
4–8 weeks ACTUAL history
```

Python, Swift, and Kotlin should produce semantically equivalent:

```text
TrainingState
CoachDecision(s)
AdaptivePlanResult
proposed PLAN
proposed evaluation
```

R should consume and analyze those artifacts.

---

# 91. Release artifacts

By v1.12 releases should include or reference:

```text
free-exercise-db-plusplus.json
exercise-relationships.json
workout-intent.schema.json
training-profile.schema.json
workout-plan.schema.json
workout.schema.json
volume-target.schema.json
coach-decision.schema.json
cross-language fixtures
package documentation
checksums
```

---

# 92. v1.12 release gate

v1.12 is complete only when:

1. WorkoutIntent is stable;
2. goal/environment resolution is deterministic;
3. target user scenario works;
4. session exercise-count constraints are enforced;
5. Python full reference works;
6. Swift SPM installs cleanly;
7. Swift end-to-end intent→plan works;
8. Swift history-aware adaptPlan works;
9. Kotlin package installs/builds cleanly;
10. Kotlin end-to-end core workflow works;
11. R package installs/checks cleanly;
12. R research workflows consume all public artifacts;
13. shared fixture parity is green;
14. package capability matrix is accurate;
15. no package depends on an LLM;
16. no network required for core operations;
17. provenance/versioning exposed;
18. all prior repository tests remain green.

---

# 93. Immediate next step — v1.10

Begin with the domain contract, not package rewrites.

Implementation order:

```text
1. ADR: WorkoutIntent vs Profile vs TARGET
2. WorkoutIntent schema
3. weekday/cycle semantics
4. exercises-per-session constraint
5. environment presets
6. goal policies
7. precedence/defaulting
8. IntentResolutionResult
9. Python resolve_intent()
10. PlanEvaluation updates
11. plan-generation integration
12. exact 5-day hypertrophy golden fixture
13. shared cross-language fixtures
14. docs/CLI
15. audit
16. full CI
17. v1.10 release
```

Only after v1.10 semantics are stable should v1.11 implement broad native-language parity.

---

# 94. Long-term definition of success

A developer should be able to use Free Exercise DB++ as a reusable domain engine rather than rebuilding training logic inside an app.

Apple app:

```text
LLM
→ WorkoutIntent
→ FreeExerciseDBPlusPlus SPM
→ PLAN / CoachDecision
→ app UI
```

Android app:

```text
LLM or form input
→ WorkoutIntent
→ Kotlin package
→ PLAN / CoachDecision
→ app UI
```

Python system:

```text
API/form/LLM adapter
→ WorkoutIntent
→ Python package
→ PLAN / CoachDecision
```

Research:

```text
WorkoutIntent / PLAN / ACTUAL
→ R/Python
→ reproducible analysis
```

The core engine remains:

```text
deterministic
portable
explainable
versioned
cross-language
offline-capable
privacy-neutral
UI-independent
LLM-independent
```

That is the target identity of Free Exercise DB++ by v1.12.
