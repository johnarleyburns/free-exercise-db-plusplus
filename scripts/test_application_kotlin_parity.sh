#!/usr/bin/env bash
set -euo pipefail

# External JVM consumer for the transport-neutral application contract.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
out=$(mktemp -d)
trap 'rm -rf "$consumer" "$out"' EXIT
mkdir -p "$consumer/src/main/kotlin"
gradle_bin=${GRADLE_BIN:-"$repo/packages/kotlin/fedbpp/gradlew"}
"$gradle_bin" --no-daemon --project-dir "$repo/packages/kotlin/fedbpp" :fedbpp:jar >/dev/null

cat > "$consumer/settings.gradle.kts" <<EOF
pluginManagement { repositories { mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { mavenCentral() } }
rootProject.name = "application-contract-consumer"
EOF
cat > "$consumer/build.gradle.kts" <<EOF
plugins { kotlin("jvm") version "2.0.21"; kotlin("plugin.serialization") version "2.0.21"; application }
repositories { mavenCentral() }
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation(files("$repo/packages/kotlin/fedbpp/fedbpp/build/libs/fedbpp.jar"))
}
kotlin { jvmToolchain(17) }
application { mainClass.set("ApplicationParityKt") }
EOF
cat > "$consumer/src/main/kotlin/ApplicationParity.kt" <<'EOF'
import java.io.File
import com.fedbpp.TrainingEngine
import com.fedbpp.TrainingRequest
import com.fedbpp.processTrainingRequest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.decodeFromStream
import kotlinx.serialization.json.encodeToStream

fun main(args: Array<String>) {
    val fixtures = File(args[0])
    val output = File(args[1]).also { it.mkdirs() }
    val json = Json { ignoreUnknownKeys = true; explicitNulls = true; encodeDefaults = false }
    val engine = TrainingEngine.bundled()
    fixtures.listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }.forEach { fixture ->
        val request = json.decodeFromStream<TrainingRequest>(fixture.resolve("request.json").inputStream())
        val result = engine.processTrainingRequest(request)
        val target = output.resolve(fixture.name).also { it.mkdirs() }.resolve("actual-result.json")
        target.outputStream().use { json.encodeToStream(result, it) }
    }
}
EOF
"$gradle_bin" --no-daemon -p "$consumer" run --args="'$repo/fixtures/application-integration' '$out'" >/dev/null
while IFS= read -r expected; do
    relative=${expected#"$repo/fixtures/application-integration/"}
    echo "Kotlin application parity: ${relative%expected-result.json}"
    python3 "$repo/tools/compare_canonical_json.py" "$expected" "$out/${relative%expected-result.json}actual-result.json" || {
        echo "Actual result: $out/${relative%expected-result.json}actual-result.json" >&2
        cat "$out/${relative%expected-result.json}actual-result.json" >&2
        exit 1
    }
done < <(find "$repo/fixtures/application-integration" -name expected-result.json | sort)
echo "Python↔Kotlin application parity passed"
