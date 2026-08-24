# FreeExerciseDBPlusPlus Swift package

Swift 6, Foundation-only consumer helpers for the DB++ exercise database and Workout 0.2 interchange format. The package is read-only and preserves direct/indirect/stabilizer semantics (1.0/0.5/0.0).

```swift
let db = try FEDatabase.load(url: databaseURL)
let workout = try Workout.load(url: workoutURL)
let volume = workout.effectiveSets(using: db)
```

Run tests with `swift test` from `packages/swift/FreeExerciseDBPlusPlus`.
