# Swift getting started

The Swift package is a Foundation-only offline engine for iOS 15+, macOS 12+,
watchOS 8+, and Swift 6. It bundles the database, relationships, policies,
and schemas.

## Install

In Xcode, choose **File → Add Package Dependencies** and enter:

`https://github.com/johnarleyburns/free-exercise-db-plusplus.git`

Choose **Up to Next Major Version** from `1.15.3`. In `Package.swift`:

```swift
.package(url: "https://github.com/johnarleyburns/free-exercise-db-plusplus.git",
         from: "1.15.3")
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

## Complete runnable history and adaptation example

The external [Swift example project](../examples/app-integration/swift/) is a
copy-pasteable SPM consumer. Its
[main.swift](../examples/app-integration/swift/Sources/AppIntegration/main.swift)
loads a standalone persisted request resource, extracts a current PLAN,
TrainingProfile, VolumeTarget, and TrainingHistory, then runs state derivation,
progression, and adaptation with an explicit `asOf`. Run it with:

```sh
swift run --package-path examples/app-integration/swift AppIntegration
```

The persisted-document calls used by that example are ordinary Foundation
Codable calls (plain `JSONDecoder`/`JSONEncoder`; no custom decoder is needed):

```swift
let history = try JSONDecoder().decode(TrainingHistory.self, from: historyData)
let plan = try JSONDecoder().decode(WorkoutPlan.self, from: planData)
let profile = try JSONDecoder().decode(TrainingProfile.self, from: profileData)
let target = try JSONDecoder().decode(VolumeTarget.self, from: targetData)
let persistedPlanJSON = try JSONEncoder().encode(plan)
```

For native construction, use the public
`TrainingHistory(subjectId:plans:workouts:targets:planActivations:metadata:)`
initializer. State derivation returns `state_derived`; progression returns
`progression_available` or `insufficient_data`; adaptation returns
`no_change`, `revision_proposed`, or `regeneration_proposed` when a proposal is
available. Also handle `invalid`/`invalid_input` and `unsatisfiable` as shown
in the example. DB++ proposes only: the host app decides whether to display,
persist, approve, or activate a proposed revision.

All public application models are typed, `Codable`, `Sendable`, and
`Equatable` where meaningful. Keep canonical JSON as the persistence boundary;
the package's `JSONValue` is only for open-ended extension fields.
