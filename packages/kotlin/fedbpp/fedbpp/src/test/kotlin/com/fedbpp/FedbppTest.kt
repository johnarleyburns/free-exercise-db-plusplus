package com.fedbpp

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class FedbppTest {
    @Test fun databaseLoadsAndQueries() {
        val root = generateSequence(File(".").absoluteFile) { it.parentFile }.first { File(it, "free-exercise-db-plusplus.json").exists() }
        val db = Database.load(File(root, "free-exercise-db-plusplus.json"))
        assert(db.size > 800)
        assertEquals("Bench_Dips", db.getExercise("Bench_Dips").exerciseId)
    }
    @Test fun effectiveSetsAndHealthConnectPreserveIds() {
        val db = Database.load(File("../../../free-exercise-db-plusplus.json"))
        val workout = Workout("0.2.0", "s", "2026-01-01T00:00:00Z", "2026-01-01T00:10:00Z", exercises = listOf(ExerciseObservation("Bench_Dips", "Bench dips", 1, sets = listOf(SetObservation(1, "working", reps = 8, completed = true)))))
        assert(workout.effectiveSets(db).isNotEmpty())
        assertEquals("Bench_Dips", workout.toHealthConnect().segments.single().dbppExerciseId)
    }
    @Test fun invalidWorkoutRejected() { assertFailsWith<ValidationException> { Workout("0.1.0", "", "", exercises = emptyList()).validate() } }
}
