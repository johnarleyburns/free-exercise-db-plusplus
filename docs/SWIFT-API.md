# Swift application API

FreeExerciseDBPlusPlus is a small, offline Swift Package Manager domain engine.
The core imports Foundation only. It does not import UIKit, SwiftUI, AppKit, or
Apple Foundation Models, and it never starts Python, a subprocess, or a network
request.

## Stable entry point

```swift
import FreeExerciseDBPlusPlus

let engine = try TrainingEngine.bundled()
```

`bundled()` loads the immutable DB++ database and relationship resources needed
by the engine; the package also ships the versioned policy/schema artifacts used
for offline distribution and validation. A custom database remains available
for tests or specialized deployments:

```swift
let engine = TrainingEngine(database: customDatabase,
                            relationships: customRelationships)
```

The engine builds deterministic read-only indexes at initialization. There is
no mutable semantic cache or hidden current-time dependency.

## Domain boundary

- `WorkoutIntent` is a structured request produced by the host app or its own
  natural-language/LLM adapter.
- `TrainingProfile` describes stable subject, availability, equipment, and
  preference context.
- `VolumeTarget` is a desired TARGET range, separate from a PLAN prescription.
- `WorkoutPlan` is a PLAN: what should be done.
- `Workout` is ACTUAL: what was recorded, including completed sets and
  canonical substitution references.
- `TrainingHistory` groups persisted PLAN, ACTUAL, TARGET, and activation data.
- `TrainingState` is a deterministic read model derived from history at an
  explicit `Date`.

The consuming application owns parsing, UI, persistence, sync, accounts,
notifications, and activation/approval decisions.

## Intent and planning

```swift
let intent = WorkoutIntent(
    goal: "hypertrophy",
    environment: "commercial_gym",
    schedule: WorkoutSchedule(
        cycleLengthDays: 7,
        sessionsPerCycle: IntRange(target: 5),
        preferredWeekdays: ["monday", "tuesday", "wednesday", "thursday", "saturday"]),
    sessionConstraints: SessionConstraints(
        exercisesPerSession: IntRange(min: 3, max: 4)))

let validation = engine.validateIntent(intent)
let resolution = engine.resolveIntent(intent)
let result = engine.generatePlanFromIntent(intent)
```

Validation and resolution are structured results. A clarification result has
`missingInformation`, and an invalid or contradictory result has structured
`conflicts`; the host app decides which question or UI to show. No invented
defaults are required beyond the released policy documents.

For an already resolved typed context, use `PlanGenerationRequest` and inspect
`GeneratedPlanResult.status`, `plan`, `evaluation`, and machine-readable issue
arrays. Normal unsatisfiable or target-gap outcomes are not thrown.

## History and coaching

```swift
let state = try engine.deriveTrainingState(
    history: history,
    asOf: asOfDate,
    window: .last28Days)

let decisions = engine.suggestProgression(plan: plan, state: state)
let adapted = engine.adaptPlan(request: PlanAdaptationRequest(
    profile: profile, target: target, currentPlan: plan,
    history: history, asOf: asOfDate))
```

Adaptive results are advisory and do not mutate the input PLAN. The app decides
whether to persist a proposed revision, present `CoachDecision` values, or
activate anything. Timestamp boundaries are offset-aware and future ACTUAL
observations are excluded relative to the supplied `asOf` instant.

## Codable and determinism

`WorkoutIntent`, `TrainingProfile`, `VolumeTarget`, `Workout`, `WorkoutPlan`,
`TrainingHistory`, `TrainingState`, `PlanEvaluation`, `CoachDecision`,
`GeneratedPlanResult`, and `AdaptivePlanResult` are Codable, Sendable, and
Equatable where applicable. Dates passed to the facade are converted to stable
ISO-8601 instants; derived state retains its canonical string representation.

Repeated calls with identical values and explicit `asOf` inputs produce the
same semantic result. The engine does not call `Date()`, create UUIDs, use
randomness, or expose unordered candidate selection.

## Errors and JSON compatibility

Use thrown errors for unavailable/corrupt packaged resources and malformed
serialized documents. Domain outcomes such as clarification, invalid intent,
unsatisfiable generation, insufficient history, and no adaptation are returned
with stable status and reason fields.

`JSONValue` remains available only where the canonical schemas intentionally
allow open-ended metadata, detailed evidence, policy documents, and future
extensions. New app workflows use typed request/result models. The v1.11
JSON-oriented instance helpers are retained under explicit `*JSON` names as
deprecated migration shims; they forward to the same native implementations.

## LLM boundary

An app may use Apple Foundation Models or another system to map conversation
output into `WorkoutIntent`. That adapter is outside this package. DB++ accepts
the structured intent and performs deterministic validation, resolution,
generation, evaluation, state derivation, progression, and coaching.
