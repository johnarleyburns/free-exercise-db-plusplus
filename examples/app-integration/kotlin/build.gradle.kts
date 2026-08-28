plugins { kotlin("jvm") version "2.0.21"; kotlin("plugin.serialization") version "2.0.21"; application }
repositories { mavenCentral() }
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation(files("../../../packages/kotlin/fedbpp/fedbpp/build/libs/fedbpp.jar"))
}
kotlin { jvmToolchain(17) }
application { mainClass.set("AppIntegrationKt") }
