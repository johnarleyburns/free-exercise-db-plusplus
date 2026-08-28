#!/usr/bin/env bash
set -euo pipefail

# This is intentionally an external consumer smoke test.  It is run by CI on
# hosts with the Gradle wrapper/toolchain and is independent of the checkout
# cwd and source-tree-relative resources.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
trap 'rm -rf "$consumer"' EXIT
mkdir -p "$consumer/src/main/kotlin"
cp "$repo/fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json" "$consumer/intent.json"
cp "$repo/fixtures/cross-language/generation/input.json" "$consumer/generation.json"
gradle_bin=${GRADLE_BIN:-"$repo/packages/kotlin/fedbpp/gradlew"}
# Build the artifact consumed below.  Keeping this before the temporary
# project is important: the consumer must exercise the packaged JAR, not the
# checkout's compiled classes.
"$gradle_bin" --no-daemon --project-dir "$repo/packages/kotlin/fedbpp" :fedbpp:jar
cat > "$consumer/settings.gradle.kts" <<EOF
pluginManagement { repositories { mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { mavenCentral() } }
rootProject.name = "consumer"
EOF
cat > "$consumer/build.gradle.kts" <<EOF
plugins { kotlin("jvm") version "2.0.21"; kotlin("plugin.serialization") version "2.0.21"; application }
repositories { mavenCentral() }
dependencies { implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3"); implementation(files("$repo/packages/kotlin/fedbpp/fedbpp/build/libs/fedbpp.jar")) }
kotlin { jvmToolchain(17) }
application { mainClass.set("ConsumerKt") }
EOF
cat > "$consumer/src/main/kotlin/Consumer.kt" <<'EOF'
import java.io.File
import java.time.Instant
import com.fedbpp.*
import kotlinx.serialization.json.*
fun main(args: Array<String>) {
    val json = Json { ignoreUnknownKeys = true }
    val engine = TrainingEngine.bundled()
    check(engine.database.size > 800)
    val intent = decodeWorkoutIntent(File(args[0]).readText())
    val result = engine.resolveIntent(intent)
    check(result.status == "resolved_with_defaults")
    check(result.goalPolicy?.policyId == "general-hypertrophy-v1")
    val request = json.parseToJsonElement(File(args[1]).readText()).jsonObject
    val profile = json.decodeFromJsonElement(TrainingProfile.serializer(), request["profile"]!!)
    val target = json.decodeFromJsonElement(VolumeTarget.serializer(), request["target"]!!)
    val generated = engine.generatePlan(PlanGenerationRequest(profile, target, request["policy"]!!.toString().trim('"'), requiredExerciseIds = listOf("Barbell_Bench_Press_-_Medium_Grip")))
    check(generated.status == "generated")
    check(generated.plan != null && engine.evaluatePlan(generated.plan!!, profile, target).toJson() == generated.evaluation!!.toJson())
    val history = TrainingHistory("consumer", plans = listOf(generated.plan!!))
    val state = engine.deriveTrainingState(history, Instant.parse("2026-08-28T00:00:00Z"), target = target)
    check(state.subjectId == "consumer")
    check(engine.suggestProgression(generated.plan!!, state).isNotEmpty())
    val roundTrip = json.decodeFromJsonElement(WorkoutPlan.serializer(), json.encodeToJsonElement(WorkoutPlan.serializer(), generated.plan!!))
    check(roundTrip == generated.plan)
    println("kotlin consumer ok")
}
EOF
"$gradle_bin" -p "$consumer" run --args="${consumer}/intent.json ${consumer}/generation.json" --no-daemon
