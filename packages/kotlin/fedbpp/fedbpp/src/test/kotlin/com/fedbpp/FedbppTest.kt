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
import kotlinx.serialization.json.doubleOrNull

class FedbppTest {
    @Test fun generatorContinuesFromMinimumToMuscleTarget() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-target", ".json").toFile()
        dbFile.writeText("""{"metadata":{},"exercises":{"press":{"exerciseId":"press","annotation":{"direct":["chest"],"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"cycleLengthDays":7,"sessionsPerCycle":{"target":1},"exercisesPerSession":{"min":1,"max":2}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{"chest":{"min":1,"target":3,"max":3}}}""")
        val result = generatePlan(profile, target, Database.load(dbFile)).jsonObject
        assertEquals("generated", result["status"]!!.jsonPrimitive.content)
        assertEquals(3.0, result["evaluation"]!!.jsonObject["muscleCoverage"]!!.jsonObject["chest"]!!.jsonObject["actualEffectiveSets"]!!.jsonPrimitive.doubleOrNull)
        dbFile.delete()
    }

    @Test fun generatorFillsSessionMinimumWithDistinctExercises() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-session-min", ".json").toFile()
        dbFile.writeText("""{"metadata":{},"exercises":{"a":{"exerciseId":"a","annotation":{"volumeEligible":true},"source":{"equipment":"barbell"}},"b":{"exerciseId":"b","annotation":{"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"cycleLengthDays":7,"sessionsPerCycle":{"target":1},"exercisesPerSession":{"min":2,"max":2}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{}}""")
        val result = generatePlan(profile, target, Database.load(dbFile)).jsonObject
        assertEquals("generated", result["status"]!!.jsonPrimitive.content)
        assertEquals(listOf("a", "b"), result["plan"]!!.jsonObject["sessions"]!!.jsonArray.single().jsonObject["exercises"]!!.jsonArray.map { it.jsonObject["exerciseId"]!!.jsonPrimitive.content })
        dbFile.delete()
    }

    @Test fun generatorAllocatesMovementPatternMinimum() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-pattern", ".json").toFile()
        dbFile.writeText("""{"metadata":{},"exercises":{"press":{"exerciseId":"press","annotation":{"direct":["chest"],"patterns":["horizontal_press"],"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"cycleLengthDays":7,"sessionsPerCycle":{"target":1},"exercisesPerSession":{"min":1,"max":2}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{},"movementPatterns":{"horizontal_press":{"minimumSets":2}}}""")
        val result = generatePlan(profile, target, Database.load(dbFile)).jsonObject
        assertEquals("generated", result["status"]!!.jsonPrimitive.content)
        assertEquals(2.0, result["evaluation"]!!.jsonObject["movementPatterns"]!!.jsonObject["horizontal_press"]!!.jsonObject["plannedSets"]!!.jsonPrimitive.doubleOrNull)
        dbFile.delete()
    }

    @Test fun generatorDistributesFrequencyAcrossSessions() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-frequency", ".json").toFile()
        dbFile.writeText("""{"metadata":{},"exercises":{"press":{"exerciseId":"press","annotation":{"direct":["chest"],"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"cycleLengthDays":7,"sessionsPerCycle":{"target":2},"exercisesPerSession":{"min":1,"max":2}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{},"frequency":{"muscles":{"chest":{"min":2}}}}""")
        val result = generatePlan(profile, target, Database.load(dbFile)).jsonObject
        assertEquals("generated", result["status"]!!.jsonPrimitive.content)
        assertEquals(2.0, result["evaluation"]!!.jsonObject["frequency"]!!.jsonObject["chest"]!!.jsonObject["normalizedExposuresPer7Days"]!!.jsonPrimitive.doubleOrNull)
        dbFile.delete()
    }

    @Test fun generatorAllocatesMuscleMinimumThroughNativeEvaluator() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-generator", ".json").toFile()
        dbFile.writeText("""{"metadata":{"setCredits":{"direct":1,"indirect":0.5,"stabilizer":0}},"exercises":{"chest":{"exerciseId":"chest","annotation":{"direct":["chest"],"volumeEligible":true},"source":{"equipment":"barbell"}},"legs":{"exerciseId":"legs","annotation":{"direct":["quadriceps"],"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"cycleLengthDays":7,"sessionsPerCycle":{"target":1},"exercisesPerSession":{"min":1,"max":3}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{"chest":{"min":2}}}""")
        val generated = generatePlan(profile, target, Database.load(dbFile)).jsonObject
        assertEquals("generated", generated["status"]!!.jsonPrimitive.content)
        assertEquals(2, generated["plan"]!!.jsonObject["sessions"]!!.jsonArray.single().jsonObject["exercises"]!!.jsonArray.single().jsonObject["sets"]!!.jsonPrimitive.intOrNull)
        dbFile.delete()
    }

    @Test fun targetContributionUsesAuthoritativeCustomCredits() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-credit", ".json").toFile()
        dbFile.writeText("""{"metadata":{"setCredits":{"direct":1,"indirect":0.25,"stabilizer":0.1}},"exercises":{"x":{"exerciseId":"x","annotation":{"direct":["chest"],"indirect":["triceps"],"stabilizers":["core"],"patterns":["horizontal_press"],"volumeEligible":true}}}}""")
        val db = Database.load(dbFile); val candidate = PlanningCandidate("x", "press", null, db.getExercise("x").annotation)
        assertEquals(0.25, targetContribution(candidate, "muscle", "triceps", db)); assertEquals(0.1, targetContribution(candidate, "muscle", "core", db)); assertEquals(1.0, targetContribution(candidate, "pattern", "horizontal_press", db))
        dbFile.delete()
    }

    @Test fun sessionCountOrderingMatchesCanonicalPlanner() {
        assertEquals(listOf(4, 3, 5, 2), canonicalSessionCounts(2, 4, 5, 3).counts)
        assertEquals(listOf("SESSION_COUNT_CONFLICT"), canonicalSessionCounts(0, 0, 0, 3).conflicts)
        assertEquals(listOf(2), canonicalSessionCounts(0, 1, 2, 3, policyMinimum = 2).counts)
    }

    @Test fun candidateRankingMatchesPythonPriorityAndLexicalTieBreak() {
        val a = PlanningCandidate("a", null, null, ExerciseAnnotation(volumeEligible = true))
        val b = PlanningCandidate("b", null, null, ExerciseAnnotation(volumeEligible = true))
        val c = PlanningCandidate("c", null, null, ExerciseAnnotation(volumeEligible = true))
        assertEquals(listOf("c", "b", "a"), rankCandidates(listOf(a, b, c), setOf("c"), emptySet(), preferred = setOf("b")) { 1.0 }.map { it.exerciseId })
        assertEquals(listOf("a", "b"), rankCandidates(listOf(b, a), emptySet(), emptySet()) { 1.0 }.map { it.exerciseId })
    }

    @Test fun candidatePoolAppliesEquipmentExclusionsAndVolumeEligibility() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-planning", ".json").toFile()
        dbFile.writeText("""{"metadata":{},"exercises":{"a":{"exerciseId":"a","annotation":{"volumeEligible":true},"source":{"equipment":"barbell"}},"b":{"exerciseId":"b","annotation":{"volumeEligible":true},"source":{"equipment":"dumbbell"}},"c":{"exerciseId":"c","annotation":{"volumeEligible":false},"source":{"equipment":"barbell"}}}}""")
        val profile = Json.parseToJsonElement("""{"equipment":["barbell"],"constraints":{"excludedExerciseIds":["a"]}}""").jsonObject
        assertEquals(emptyList(), canonicalCandidatePool(Database.load(dbFile), profile).map { it.exerciseId })
        assertEquals(listOf("a"), canonicalCandidatePool(Database.load(dbFile), Json.parseToJsonElement("""{"equipment":["barbell"]}""").jsonObject).map { it.exerciseId })
        dbFile.delete()
    }

    @Test fun canonicalDayOffsetsMatchFlagshipPythonTieBreaking() {
        assertEquals(listOf(0, 1, 2, 3, 5), canonicalDayOffsets(7, 5, listOf(0, 1, 2, 3, 5), emptySet()))
        assertEquals(listOf(0, 1, 3), canonicalDayOffsets(6, 3, emptyList(), emptySet()))
    }

    @Test fun trainingStateExcludesFutureWorkoutOnSameUtcDay() {
        val history = Json.parseToJsonElement("""{"subjectId":"s","workouts":[{"startTime":"2026-08-25T11:00:00Z","exercises":[{"exerciseId":"before","sets":[{"completed":true}]}]},{"startTime":"2026-08-25T13:00:00Z","exercises":[{"exerciseId":"after","sets":[{"completed":true}]}]}],"plans":[],"planActivations":[]}""")
        val state = deriveTrainingState(history, "2026-08-25T12:00:00Z").jsonObject["exerciseState"]!!.jsonObject
        assertEquals(setOf("before"), state.keys)
    }

    @Test fun nativePlanEvaluatorUsesDatabaseSetCreditsAndReportsTargetState() {
        val dbFile = kotlin.io.path.createTempFile("fedbpp-evaluation", ".json").toFile()
        dbFile.writeText("""{"metadata":{"schemaVersion":"1.0.0","setCredits":{"direct":1.0,"indirect":0.25,"stabilizer":0.0}},"exercises":{"press":{"exerciseId":"press","annotation":{"direct":["chest"],"indirect":["triceps"],"patterns":["horizontal_press"],"volumeEligible":true},"source":{"equipment":"barbell"}}}}""")
        val plan = Json.parseToJsonElement("""{"schemaVersion":"0.2.0","planId":"p","revisionId":"r1","cycle":{"lengthDays":7},"sessions":[{"planSessionId":"s1","dayOffset":0,"exercises":[{"prescriptionId":"rx1","exerciseId":"press","sets":4}]}]}""")
        val profile = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","equipment":["barbell"],"availability":{"sessionsPerCycle":{"min":1,"max":1},"exercisesPerSession":{"min":1,"max":1}}}""")
        val target = Json.parseToJsonElement("""{"schemaVersion":"0.1.0","targetId":"t","periodDays":7,"muscles":{"chest":{"min":4,"target":4,"max":4},"triceps":{"target":1}},"frequency":{"muscles":{"chest":{"min":1}}},"movementPatterns":{"horizontal_press":{"minimumSets":4}}}""")
        val result = evaluatePlan(plan, Database.load(dbFile), profile, target).jsonObject
        assertEquals(4.0, result["muscleCoverage"]!!.jsonObject["chest"]!!.jsonObject["actualEffectiveSets"]!!.jsonPrimitive.doubleOrNull)
        assertEquals(1.0, result["muscleCoverage"]!!.jsonObject["triceps"]!!.jsonObject["actualEffectiveSets"]!!.jsonPrimitive.doubleOrNull)
        assertEquals("valid", result["summary"]!!.jsonObject["evaluationStatus"]!!.jsonPrimitive.content)
        dbFile.delete()
    }
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
        val sessions = generatePlanFromIntent(flagship, db).jsonObject["generation"]!!.jsonObject["plan"]!!.jsonObject["sessions"]!!.jsonArray
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
