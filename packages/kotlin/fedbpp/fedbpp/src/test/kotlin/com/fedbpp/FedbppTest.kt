package com.fedbpp

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.intOrNull

class FedbppTest {
    @Test fun workoutIntentFlagshipResolvesNatively() {
        val intent = WorkoutIntent(goal = "hypertrophy", environment = "commercial_gym", schedule = WorkoutSchedule(7, IntRangeValue(target = 5), preferredWeekdays = listOf("monday", "tuesday", "wednesday", "thursday", "saturday")))
        val result = resolveIntent(intent)
        assertEquals("resolved_with_defaults", result.status)
        assertEquals("general-hypertrophy-v1", result.goalPolicy?.policyId)
        assertEquals(listOf("goalPolicy", "planningPolicy", "environmentPolicy"), result.defaultsApplied)
        val profile = result.resolvedProfile as kotlinx.serialization.json.JsonObject
        assertEquals("commercial-gym-general-v1", result.environmentPolicy)
        assertEquals("[0,1,2,3,5]", (profile["availability"] as kotlinx.serialization.json.JsonObject)["preferredDayOffsets"]?.toString())
    }
    @Test fun workoutIntentGoalMismatchIsStructured() {
        val intent = WorkoutIntent(goal = "hypertrophy", requestedGoalPolicy = "general-strength-v1", environment = "commercial_gym", schedule = WorkoutSchedule(7, IntRangeValue(target = 3)))
        val result = resolveIntent(intent)
        assertEquals("invalid", result.status); assertEquals("GOAL_POLICY_MISMATCH", result.conflicts.single().code); assertEquals(ExplicitOverrides(), result.explicitOverrides)
    }
    @Test fun workoutIntentDbAwareValidationMatchesReference() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "free-exercise-db-plusplus.json").exists() }
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        val bad = WorkoutIntent(goal = "hypertrophy", environment = "commercial_gym", schedule = WorkoutSchedule(7, IntRangeValue(target = 3)), exerciseConstraints = ExerciseConstraints(requiredExerciseIds = listOf("does-not-exist")), equipmentOverrides = EquipmentOverrides(addEquipment = listOf("does-not-exist")))
        val errors = validateWorkoutIntent(bad, db)
        assert(errors.any { it.contains("unknown exerciseId") }); assert(errors.any { it.contains("unknown DB++ equipment") })
    }
    @Test fun everyCanonicalNonHistoryFixtureResolves() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "fixtures/cross-language/intent").isDirectory }
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        val json = Json { ignoreUnknownKeys = true; explicitNulls = false; encodeDefaults = true }
        File(root, "fixtures/cross-language/intent").listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }.filterNot { File(it, "history.json").exists() }.forEach { fixture ->
            val intent = json.decodeFromString<WorkoutIntent>(File(fixture, "input.json").readText())
            val target = File(fixture, "target.json").takeIf { it.exists() }?.let { json.parseToJsonElement(it.readText()) }
            val actual = json.encodeToJsonElement(IntentResolutionResult.serializer(), resolveIntent(intent, db, target = target))
            val expected = json.parseToJsonElement(File(fixture, "expected-resolution.json").readText())
            val stableTopLevel = listOf("resolvedProfile", "resolvedTarget", "planningPolicy", "goalPolicy", "environmentPolicy")
            val normalized = if (actual is JsonObject) JsonObject(actual.toMutableMap().apply { stableTopLevel.forEach { key -> if (!containsKey(key)) put(key, kotlinx.serialization.json.JsonNull) } }) else actual
            assert(normalized == expected) { fixture.name }
        }
    }
    @Test fun historyAndGenerationUseCanonicalWindowAndOffsets() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "fixtures/cross-language/intent").isDirectory }
        val json = Json { ignoreUnknownKeys = true; explicitNulls = false; encodeDefaults = true }
        val historyDir = File(root, "fixtures/cross-language/intent/history-aware")
        val intent = json.decodeFromString<WorkoutIntent>(File(historyDir, "input.json").readText())
        val result = resolveIntent(intent, history = json.parseToJsonElement(File(historyDir, "history.json").readText()), asOf = "2026-08-25T12:00:00Z")
        assertEquals("r1", result.generationOptions.jsonObject["trainingState"]!!.jsonObject["activePlan"]!!.jsonObject["revisionId"]!!.jsonPrimitive.content)
        assertEquals(1, result.generationOptions.jsonObject["trainingState"]!!.jsonObject["exerciseState"]!!.jsonObject["Barbell_Bench_Press_-_Medium_Grip"]!!.jsonObject["recentSessionCount"]!!.jsonPrimitive.intOrNull)
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        val flagship = json.decodeFromString<WorkoutIntent>(File(root, "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json").readText())
        val sessions = generatePlanFromIntent(flagship, db).jsonObject["generation"]!!.jsonObject["sessions"]!!.jsonArray
        assertEquals(listOf(0, 1, 2, 3, 5), sessions.map { it.jsonObject["dayOffset"]!!.jsonPrimitive.intOrNull })
    }
    @Test fun databaseLoadsAndQueries() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "free-exercise-db-plusplus.json").exists() }
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        assert(db.size > 800)
        assertEquals("Bench_Dips", db.getExercise("Bench_Dips").exerciseId)
    }
    @Test fun effectiveSetsAndHealthConnectPreserveIds() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "free-exercise-db-plusplus.json").exists() }
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        val workout = Workout("0.2.0", "s", "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", exercises = listOf(ExerciseObservation("Bench_Dips", "Bench dips", 1, sets = listOf(SetObservation(1, "working", reps = 8, completed = true)))))
        assert(workout.effectiveSets(db).isNotEmpty())
        assertEquals("Bench_Dips", workout.toHealthConnect().segments.single().dbppExerciseId)
    }
    @Test fun invalidWorkoutRejected() { assertFailsWith<ValidationException> { Workout("0.1.0", "", "", exercises = emptyList()).validate() } }
    @Test fun relationshipArtifactLookup() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "exercise-relationships.json").exists() }
        val relationships = loadRelationships(File(root, "exercise-relationships.json"))
        assertEquals("bench_press", relationships.familyFor("Dumbbell_Bench_Press")?.familyId)
        assert("Barbell_Bench_Press_-_Medium_Grip" in relationships.members("bench_press"))
    }
}
