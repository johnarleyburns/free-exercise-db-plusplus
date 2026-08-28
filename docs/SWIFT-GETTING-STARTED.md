# Swift getting started

The Swift package is a Foundation-only offline engine for iOS 15+, macOS 12+,
watchOS 8+, and Swift 6. It bundles the database, relationships, policies,
and schemas.

## Install

In Xcode, choose **File → Add Package Dependencies** and enter:

`https://github.com/johnarleyburns/free-exercise-db-plusplus.git`

Choose **Up to Next Major Version** from `1.15.0`. In `Package.swift`:

```swift
.package(url: "https://github.com/johnarleyburns/free-exercise-db-plusplus.git",
         from: "1.15.0")
```

Then `import FreeExerciseDBPlusPlus` and initialize `try TrainingEngine.bundled()`.
The package has no Python, Java, Android SDK, network, or LLM requirement.

## Which object do I need?

| Need | DB++ object |
| --- | --- |
| User request | `WorkoutIntent` |
| Schedule/equipment/preferences | `TrainingProfile` |
| Desired volume | `VolumeTarget` |
| What should happen | `TrainingRequest` |
| Prescribed work | `WorkoutPlan` |
| Completed work | `Workout` |
| Historical collection | `TrainingHistory` |
| Derived current state | `TrainingState` |
| Evaluation | `PlanEvaluation` |
| Proposed changes | `CoachDecision` / `AdaptivePlanResult` |
| Application outcome | `TrainingResult` |

## End-to-end request

The typed facade is explicit about new-plan generation versus adaptation:

```swift
import FreeExerciseDBPlusPlus

let engine = try TrainingEngine.bundled()
let intent = WorkoutIntent(
  intentId: "intent-1", subjectId: "user-123", goal: "hypertrophy",
  environment: "commercial_gym",
  schedule: WorkoutSchedule(cycleLengthDays: 7,
    sessionsPerCycle: IntRange(target: 5),
    preferredWeekdays: ["monday", "tuesday", "wednesday", "thursday", "saturday"]),
  sessionConstraints: SessionConstraints(exercisesPerSession: IntRange(min: 3, max: 4)),
  useHistory: true, historyWindow: "last_28_days")
let request = TrainingRequest(requestId: "request-1",
                              operation: .generateFromIntent, intent: intent)
let result = try engine.processTrainingRequest(request)

switch result.status {
case "needs_clarification": print(result.missingInformation)
case "generated", "generated_with_target_gaps": print(result.plan as Any)
case "invalid", "unsatisfiable": print(result.issues)
default: print(result.status)
}
```

For persisted documents, decode with `JSONDecoder` into the same public
`Codable` types. Native history construction uses the real public initializer:

```swift
let history = TrainingHistory(subjectId: "user-123", plans: [], workouts: [],
                              targets: [], planActivations: [])
let historyRequest = TrainingRequest(requestId: "request-history",
  operation: .generateFromIntent, intent: intent, history: history,
  asOf: "2026-08-28T12:00:00Z")
let historyResult = try engine.processTrainingRequest(historyRequest)
```

Use `TrainingHistory(subjectId:plans:workouts:targets:planActivations:metadata:)`
for native values, or `JSONDecoder().decode(TrainingHistory.self, from:)` for
persisted JSON. `Workout`, `WorkoutPlan`, `TrainingProfile`, and `VolumeTarget`
are decoded in the same way.

## Existing PLAN, state, progression, and adaptation

```swift
let plan: WorkoutPlan = /* decode persisted PLAN JSON */ fatalError("load PLAN")
let target: VolumeTarget = /* decode TARGET JSON */ fatalError("load TARGET")
let profile: TrainingProfile = /* decode profile JSON */ fatalError("load profile")
let history: TrainingHistory = /* decode history JSON */ fatalError("load history")

let evaluation = try engine.processTrainingRequest(TrainingRequest(
  requestId: "evaluate-1", operation: .evaluatePlan, profile: profile,
  target: target, plan: plan))
let state = try engine.processTrainingRequest(TrainingRequest(
  requestId: "state-1", operation: .deriveState, target: target,
  history: history, asOf: "2026-08-28T12:00:00Z",
  historyWindow: .last28Days))
let adaptation = try engine.processTrainingRequest(TrainingRequest(
  requestId: "adapt-1", operation: .adaptPlan, profile: profile, target: target,
  currentPlan: plan, history: history, asOf: "2026-08-28T12:00:00Z"))
```

`evaluatePlan` returns `evaluated`, state derivation returns `state_derived`,
and adaptation returns `no_change` or `revision_proposed`. The host decides
whether to approve and activate a proposal; DB++ does not mutate or activate
the current PLAN. For direct progression, provide `plan` and a decoded
`trainingState` with operation `.suggestProgression`.

All public application models are typed, `Codable`, `Sendable`, and
`Equatable` where meaningful. Keep canonical JSON as the persistence boundary;
the package's `JSONValue` is only for open-ended extension fields.
