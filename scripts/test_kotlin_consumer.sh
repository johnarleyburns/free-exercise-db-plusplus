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
gradle_bin=${GRADLE_BIN:-gradle}
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
import com.fedbpp.*
fun main(args: Array<String>) {
    val intent = decodeWorkoutIntent(File(args[0]).readText())
    val result = resolveIntent(intent)
    check(result.status == "resolved_with_defaults")
    check(result.goalPolicy?.policyId == "general-hypertrophy-v1")
    println("kotlin consumer ok")
}
EOF
"$gradle_bin" -p "$consumer" run --args="${consumer}/intent.json" --no-daemon
