# FreeExerciseDBPlusPlus Swift package

Swift 6, Foundation-only consumer helpers for DB++, Workout ACTUAL, and Workout PLAN 0.1/0.2. PLAN Codable models preserve phases, progression, optional/conditional prescriptions, load, effort, set type, laterality, notes, and heterogeneous planned sets. Coverage reports include native and normalized seven-day views, completeness, muscle roles, movement patterns, and phase-specific results. The package is read-only and preserves direct/indirect/stabilizer semantics (1.0/0.5/0.0).

```swift
let db = try FEDatabase.load(url: databaseURL)
let workout = try Workout.load(url: workoutURL)
let volume = workout.effectiveSets(using: db)
let plan = try WorkoutPlan.load(url: planURL)
let coverage = plan.coverage(using: db)
```

Run tests with `swift test` from `packages/swift/FreeExerciseDBPlusPlus`.
