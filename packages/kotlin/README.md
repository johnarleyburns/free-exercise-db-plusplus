# FreeExerciseDBPlusPlus Kotlin package

Kotlin 2.x/JVM-compatible offline semantic engine for Android, plain JVM, and
server-side consumers. The core uses `kotlinx.serialization`, has no Android
SDK dependency, and bundles the canonical database and relationship resources.
See [docs/KOTLIN-API.md](../../docs/KOTLIN-API.md) for the application API.

```kotlin
val database = Database.load(File("free-exercise-db-plusplus.json"))
val workout = Workout.load(File("workout.json"))
val volume = workout.effectiveSets(database)
val healthConnect = workout.toHealthConnect() // preserves dbppExerciseId
```

Run `./packages/kotlin/fedbpp/gradlew --no-daemon test --project-dir packages/kotlin/fedbpp`.

Effective-set helpers read `metadata.setCredits`, exclude `volumeEligible=false`, and apply `dbpp-default-volume-v1` top-level set-type counting.

WorkoutIntent resolution is native and JVM-only:

```kotlin
val intent = WorkoutIntent(goal = "hypertrophy", environment = "commercial_gym",
    schedule = WorkoutSchedule(7, IntRangeValue(target = 5),
        preferredWeekdays = listOf("monday", "tuesday", "wednesday", "thursday", "saturday")))
val engine = TrainingEngine.bundled()
val resolution = engine.resolveIntent(intent)
val generated = engine.generatePlanFromIntent(intent)
```
