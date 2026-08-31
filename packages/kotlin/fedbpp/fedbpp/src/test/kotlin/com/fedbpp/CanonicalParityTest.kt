package com.fedbpp

import java.io.File
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlinx.serialization.json.*
import java.math.BigDecimal

class CanonicalParityTest {
    private val json = Json { ignoreUnknownKeys = true; explicitNulls = true; encodeDefaults = true }
    private fun root(): File { var p = File(".").absoluteFile; while (!File(p, "free-exercise-db-plusplus.json").exists()) p = p.parentFile ?: error("root"); return p }
    private fun e(f: File) = json.parseToJsonElement(f.readText())
    private fun mismatch(left: JsonElement, right: JsonElement, path: String = "$"): String? = when {
        left is JsonObject && right is JsonObject -> when {
            left.keys != right.keys -> "$path keys expected=${left.keys} actual=${right.keys}"
            else -> left.keys.firstNotNullOfOrNull { mismatch(left.getValue(it), right.getValue(it), "$path.$it") }
        }
        left is JsonArray && right is JsonArray -> if (left.size != right.size) "$path size expected=${left.size} actual=${right.size}" else left.indices.firstNotNullOfOrNull { mismatch(left[it], right[it], "$path[$it]") }
        left is JsonPrimitive && right is JsonPrimitive && left.isString == right.isString -> if (left.isString) if (left.content == right.content) null else "$path expected=${left.content} actual=${right.content}" else runCatching { if (BigDecimal(left.content).compareTo(BigDecimal(right.content)) == 0) null else "$path expected=${left.content} actual=${right.content}" }.getOrElse { if (left == right) null else "$path expected=$left actual=$right" }
        else -> if (left == right) null else "$path expected=$left actual=$right"
    }
    @Test fun evaluationFixtureMatches() {
        val r = root(); val input = e(File(r, "fixtures/cross-language/evaluation/input.json")).jsonObject
        val actual = evaluatePlan(input["plan"]!!, Database.load(File(r, "free-exercise-db-plusplus.json")), input["profile"], input["target"], loadRelationships(File(r, "exercise-relationships.json")))
        val expected = e(File(r, "fixtures/cross-language/evaluation/expected.json"))
        assertEquals(null, mismatch(expected, actual), "canonical evaluation fixture differs")
    }

    @Test fun evaluationVariantFixturesMatch() {
        val r = root(); val base = Database.load(File(r, "free-exercise-db-plusplus.json")); val relationships = loadRelationships(File(r, "exercise-relationships.json"))
        r.resolve("fixtures/cross-language/evaluation").listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }.forEach { dir ->
            val input = e(File(dir, "input.json")).jsonObject; val override = input["databaseOverrides"]?.jsonObject?.get("setCredits")?.jsonObject; val database = if (override == null) base else base.withSetCredits(override)
            val actual = evaluatePlan(input["plan"]!!, database, input["profile"], input["target"], relationships); val expectedFile = File(dir, "expected.json")
            assertEquals(null, mismatch(e(expectedFile), actual), "evaluation ${dir.name} differs")
        }
    }

    @Test fun progressionFixturesMatch() {
        val r = root(); val input = e(File(r, "fixtures/cross-language/progression/input.json")).jsonObject
        val actual = buildJsonObject { input["cases"]!!.jsonArray.forEach { item -> val x = item.jsonObject; put(x["id"]!!.jsonPrimitive.content, applyProgressionPolicy(input["policy"]!!.jsonPrimitive.content, x["prescription"]!!, x["state"]!!, input["parameters"])) } }
        assertEquals(null, mismatch(e(File(r, "fixtures/cross-language/progression/expected.json")), actual), "progression fixture differs")
    }

    @Test fun generationFixturesMatch() {
        val r = root(); val database = Database.load(File(r, "free-exercise-db-plusplus.json")); val relationships = loadRelationships(File(r, "exercise-relationships.json"))
        r.resolve("fixtures/cross-language/generation").listFiles()!!.filter { it.isDirectory || it.name == "input.json" }.sortedBy { it.name }.forEach { entry ->
            val dir = if (entry.isDirectory) entry else entry.parentFile
            if (entry.isDirectory.not() && entry.name != "input.json") return@forEach
            val input = e(File(dir, "input.json")).jsonObject; val required = input["requiredExerciseIds"]?.jsonArray.orEmpty().map { it.jsonPrimitive.content }; val actual = generatePlan(input["profile"]!!, input["target"]!!, database, relationships, required, buildJsonObject { put("policy", input["policy"] ?: JsonPrimitive("full-body-general-v1")); input["lockedExerciseIds"]?.let { put("lockedExerciseIds", it) }; input["additionalExclusions"]?.let { put("additionalExclusions", it) } })
            assertEquals(null, mismatch(e(File(dir, "expected.json")), actual), "generation ${dir.name} differs")
        }
    }

    @Test fun intentResolutionFixturesMatch() {
        val r = root(); val engine = TrainingEngine(Database.load(File(r, "free-exercise-db-plusplus.json")))
        r.resolve("fixtures/cross-language/intent").listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }.forEach { dir ->
            val intent = json.decodeFromJsonElement(WorkoutIntent.serializer(), e(File(dir, "input.json")))
            val historyFile = File(dir, "history.json"); val history = if (historyFile.exists()) json.parseToJsonElement(historyFile.readText()) else null
            val targetFile = File(dir, "target.json"); val target = if (targetFile.exists()) json.parseToJsonElement(targetFile.readText()) else null
            val actual = engine.resolveIntentJson(intent, target = target, history = history, asOf = if (history != null) "2026-08-25T12:00:00Z" else null)
            val expectedFile = File(dir, "expected-resolution.json")
            if (expectedFile.exists()) assertEquals(null, mismatch(e(expectedFile), apiJson.encodeToJsonElement(IntentResolutionResult.serializer(), actual)), "intent ${dir.name} differs")
            val generationFile = File(dir, "expected-generation.json")
            if (generationFile.exists()) {
                val generated = generatePlanFromIntent(intent, engine.database, target = target, history = history, asOf = if (history != null) "2026-08-25T12:00:00Z" else null)
                assertEquals(null, mismatch(e(generationFile), generated), "intent generation ${dir.name} differs")
                val generatedRoot = generated.jsonObject
                val generation = generatedRoot["generation"]?.jsonObject
                if (generation != null && generation["plan"] !is JsonNull) {
                    val standalone = evaluatePlan(generation["plan"]!!, engine.database, generatedRoot["resolution"]?.jsonObject?.get("resolvedProfile"), generatedRoot["resolution"]?.jsonObject?.get("resolvedTarget"), null)
                    assertEquals(null, mismatch(generation["evaluation"]!!, standalone), "intent generation ${dir.name} attached evaluation differs")
                }
            }
        }
    }

    @Test fun historyFixtureMatches() {
        val r = root(); val input = e(File(r, "fixtures/cross-language/history/input.json")); val history = json.decodeFromJsonElement(TrainingHistory.serializer(), input)
        val engine = TrainingEngine(Database.load(File(r, "free-exercise-db-plusplus.json")), loadRelationships(File(r, "exercise-relationships.json")))
        val actual = engine.deriveTrainingStateJson(input, Instant.parse("2026-08-27T16:00:00Z"))
        assertEquals(null, mismatch(e(File(r, "fixtures/cross-language/history/expected.json")), actual), "history fixture differs")
        assertEquals("fixture-subject", history.subjectId)
    }

    @Test fun historyVariantFixturesMatch() {
        val r = root(); val engine = TrainingEngine(Database.load(File(r, "free-exercise-db-plusplus.json")), loadRelationships(File(r, "exercise-relationships.json")))
        r.resolve("fixtures/cross-language/history").listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }.forEach { dir ->
            val input = e(File(dir, "input.json")).jsonObject
            val history = input["history"]?.jsonObject?.let { base -> buildJsonObject { base.forEach { (k, v) -> put(k, v) }; put("timezone", input["timezone"] ?: JsonPrimitive("UTC")) } } ?: input
            val actual = engine.deriveTrainingStateJson(history, Instant.parse(input["asOf"]!!.jsonPrimitive.content), target = null)
            assertEquals(null, mismatch(e(File(dir, "expected.json")), actual), "history ${dir.name} differs")
        }
    }

    @Test fun adaptationFixturesMatch() {
        val r = root(); val database = Database.load(File(r, "free-exercise-db-plusplus.json")); val relationships = loadRelationships(File(r, "exercise-relationships.json"))
        r.resolve("fixtures/cross-language/adaptation").listFiles()!!.filter { it.isDirectory || it.name == "input.json" }.sortedBy { it.name }.forEach { entry ->
            val dir = if (entry.isDirectory) entry else entry.parentFile; val input = e(File(dir, "input.json")).jsonObject
            val profile = json.decodeFromJsonElement(TrainingProfile.serializer(), input["profile"]!!); val target = json.decodeFromJsonElement(VolumeTarget.serializer(), input["target"]!!); val current = WorkoutPlan.fromJson(input["currentPlan"]!!)
            val history = input["history"]?.let { json.decodeFromJsonElement(TrainingHistory.serializer(), it) }; val request = PlanAdaptationRequest(profile, target, current, history, null, Instant.parse(input["asOf"]!!.jsonPrimitive.content), input["policy"]!!.jsonPrimitive.content)
            val actual = adaptPlanCanonical(request, database, relationships)
            assertEquals(null, mismatch(e(File(dir, "expected.json")), actual), "adaptation ${dir.name} differs")
        }
    }

    @Test fun serializationRoundTrips() {
        val r = root()
        val input = e(File(r, "fixtures/cross-language/adaptation/input.json")).jsonObject
        val profile = json.decodeFromJsonElement(TrainingProfile.serializer(), input["profile"]!!)
        val target = json.decodeFromJsonElement(VolumeTarget.serializer(), input["target"]!!)
        val plan = WorkoutPlan.fromJson(input["currentPlan"]!!)
        val history = json.decodeFromJsonElement(TrainingHistory.serializer(), input["history"]!!)
        val engine = TrainingEngine(Database.load(File(r, "free-exercise-db-plusplus.json")), loadRelationships(File(r, "exercise-relationships.json")))
        val state = engine.deriveTrainingState(history, Instant.parse(input["asOf"]!!.jsonPrimitive.content), target = target)
        val evaluation = engine.evaluatePlan(plan, profile, target)
        val generated = engine.generatePlan(PlanGenerationRequest(profile, target))
        val decisions = engine.suggestProgression(plan, state)
        val adapted = engine.adaptPlan(PlanAdaptationRequest(profile, target, plan, history, state, Instant.parse(input["asOf"]!!.jsonPrimitive.content)))
        fun <T> roundTrip(serializer: kotlinx.serialization.KSerializer<T>, value: T): T = json.decodeFromJsonElement(serializer, json.encodeToJsonElement(serializer, value))
        assertEquals(profile, roundTrip(TrainingProfile.serializer(), profile))
        assertEquals(target, roundTrip(VolumeTarget.serializer(), target))
        assertEquals(plan, roundTrip(WorkoutPlan.serializer(), plan))
        assertEquals(history, roundTrip(TrainingHistory.serializer(), history))
        assertEquals(history.workouts.first(), roundTrip(Workout.serializer(), history.workouts.first()))
        assertEquals(state, roundTrip(TrainingState.serializer(), state))
        assertEquals(evaluation, roundTrip(PlanEvaluation.serializer(), evaluation))
        assertEquals(generated, roundTrip(GeneratedPlanResult.serializer(), generated))
        decisions.forEach { assertEquals(it, roundTrip(CoachDecision.serializer(), it)) }
        assertEquals(adapted, roundTrip(AdaptivePlanResult.serializer(), adapted))
    }
}
