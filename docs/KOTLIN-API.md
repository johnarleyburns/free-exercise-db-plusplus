# Kotlin API

The Kotlin package is a plain JVM module for Android applications, server-side
JVM code, command-line tools, and unit tests. The semantic core is offline,
deterministic, independent of the Android SDK, and bundles canonical resources.

## Installation and facade

Run `./packages/kotlin/fedbpp/gradlew --no-daemon test --project-dir packages/kotlin/fedbpp`.
Applications can depend on the `fedbpp` module or its JVM artifact.

```kotlin
import com.fedbpp.*
import java.time.Instant

val engine = TrainingEngine.bundled()
val intent = WorkoutIntent(
    goal = "hypertrophy",
    environment = "commercial_gym",
    schedule = WorkoutSchedule(
        cycleLengthDays = 7,
        sessionsPerCycle = IntRangeValue(target = 5),
        preferredWeekdays = listOf("monday", "tuesday", "wednesday", "thursday", "saturday")
    )
)
val resolution = engine.resolveIntent(intent)
val generated = engine.generatePlanFromIntent(intent)
val plan = generated.generation?.plan
val evaluation = plan?.let { engine.evaluatePlan(it) }
```

The facade also exposes `validateIntent`, `deriveTrainingState`,
`suggestProgression`, and `adaptPlan`. Normal application inputs and results are
typed Kotlin models; raw JSON overloads are interoperability escape hatches.

## History, state, and adaptation

Use `java.time.Instant` for `asOf`. History filtering is instant-based,
including offset-aware timestamps and future observations.

```kotlin
val state = engine.deriveTrainingState(
    history, Instant.parse("2026-08-28T12:00:00Z"), target = target
)
val decisions = engine.suggestProgression(plan!!, state)
val adapted = engine.adaptPlan(
    PlanAdaptationRequest(profile, target, plan, history, state,
        Instant.parse("2026-08-28T12:00:00Z"))
)
```

Adaptation proposes a revision and does not activate or mutate the supplied
plan.

## Serialization, resources, and boundaries

Use `kotlinx.serialization` serializers on the public data classes.
`WorkoutPlan` and `PlanEvaluation` preserve canonical JSON documents so
optional fields, null/missing distinctions, provenance, and array order survive
round trips. `TrainingEngine.bundled()` loads package resources directly; no
repository-relative path or network connection is required.

Identical inputs, database, policy, and timestamps produce stable semantic
JSON. The core uses no current time, random IDs, Python, subprocesses,
reflection-required behavior, network, LLM, or Android classes. Android-only
adapters belong in the application layer.
