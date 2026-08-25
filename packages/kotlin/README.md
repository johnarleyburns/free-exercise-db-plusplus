# FreeExerciseDBPlusPlus Kotlin package

Kotlin 2.x/JVM-compatible consumer and Android integration helpers. It uses `kotlinx.serialization` with `ignoreUnknownKeys` for forward-compatible DB++ decoding. The Health Connect projection is platform-neutral so Android applications can construct native `ExerciseSessionRecord` and `ExerciseSegment` objects without making this package depend on the Android SDK.

```kotlin
val database = Database.load(File("free-exercise-db-plusplus.json"))
val workout = Workout.load(File("workout.json"))
val volume = workout.effectiveSets(database)
val healthConnect = workout.toHealthConnect() // preserves dbppExerciseId
```

Run `gradle test` from `packages/kotlin/fedbpp`.

Effective-set helpers read `metadata.setCredits`, exclude `volumeEligible=false`, and apply `dbpp-default-volume-v1` top-level set-type counting. Advanced PLAN/TARGET/adherence parity is not currently claimed.
