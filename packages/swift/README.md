# FreeExerciseDBPlusPlus Swift package

FreeExerciseDBPlusPlus is a Foundation-only Swift 6 domain engine for Apple
applications and command-line/server Swift. It is offline and has no Python,
subprocess, network, UIKit, SwiftUI, AppKit, or Foundation Models dependency.

```swift
import Foundation
import FreeExerciseDBPlusPlus

// Your app or LLM adapter creates the structured intent.
let intent = WorkoutIntent(
    goal: "hypertrophy",
    environment: "commercial_gym",
    schedule: WorkoutSchedule(
        cycleLengthDays: 7,
        sessionsPerCycle: IntRange(target: 5),
        preferredWeekdays: ["monday", "tuesday", "wednesday", "thursday", "saturday"]),
    sessionConstraints: SessionConstraints(
        exercisesPerSession: IntRange(min: 3, max: 4)))

let engine = try TrainingEngine.bundled()
let validation = engine.validateIntent(intent)
if validation.isValid {
    let resolution = engine.resolveIntent(intent)
    let planned = engine.generatePlanFromIntent(intent)
    if let plan = planned.generation?.plan {
        let evaluation = engine.evaluatePlan(plan)
        print(evaluation.status)
    }
}
```

For a persisted or returning user, decode the typed artifacts your app owns and
derive state at an explicit instant:

```swift
let history = try JSONDecoder().decode(TrainingHistory.self, from: historyData)
let state = try engine.deriveTrainingState(history: history, asOf: asOfDate)
let adapted = engine.adaptPlan(request: PlanAdaptationRequest(
    profile: profile, target: target, currentPlan: plan,
    history: history, asOf: asOfDate))
```

`WorkoutPlan` is PLAN (what should happen), `Workout` is ACTUAL (what was
recorded), `VolumeTarget` is TARGET (desired criteria), and `TrainingState` is
derived read-only state. Adaptive coaching returns advisory decisions and a
proposed revision; the host app chooses whether to persist or activate it.

The application-facing models support Codable round trips and stable
Equatable comparisons. Normal domain outcomes are typed results with machine-
readable statuses, conflicts, missing information, and reason codes. Corrupt
resources or malformed serialized documents are thrown as errors.

See [the stable Swift API guide](../../docs/SWIFT-API.md) for the complete
surface, resource behavior, concurrency, determinism, and migration notes.
