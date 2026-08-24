package com.fedbpp

enum class MappingQuality { EXACT, COMPATIBLE, EXTENSION_REQUIRED, UNSUPPORTED }
data class HealthConnectSegment(val dbppExerciseId: String, val title: String?, val repetitions: Int?, val weightKg: Double?, val setNumber: Int, val quality: MappingQuality, val extensions: Map<String, String> = emptyMap())
data class HealthConnectSession(val sessionId: String, val startTime: String, val endTime: String, val segments: List<HealthConnectSegment>, val notes: String? = null)

/** Platform-neutral projection; an Android app can map this to ExerciseSessionRecord/ExerciseSegment. */
fun Workout.toHealthConnect(): HealthConnectSession {
    val end = endTime ?: throw ValidationException("Health Connect requires endTime")
    val segments = exercises.flatMap { observation ->
        val id = observation.exerciseId ?: return@flatMap emptyList()
        observation.sets.map { set ->
            val extensions = mapOf("dbpp.laterality" to (observation.laterality ?: "unspecified"))
            HealthConnectSegment(id, observation.exerciseName, set.reps, set.load?.takeIf { it.unit == "kg" }?.value, set.setNumber, MappingQuality.EXTENSION_REQUIRED, extensions)
        }
    }
    return HealthConnectSession(sessionId, startTime, end, segments, notes)
}
