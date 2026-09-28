package com.fedbpp

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.decodeFromJsonElement
import kotlinx.serialization.json.encodeToJsonElement
import kotlinx.serialization.json.jsonObject

enum class MappingQuality { EXACT, COMPATIBLE, EXTENSION_REQUIRED, UNSUPPORTED }
data class HealthConnectSegment(val dbppExerciseId: String, val title: String?, val repetitions: Int?, val weightKg: Double?, val setNumber: Int, val quality: MappingQuality, val extensions: Map<String, String> = emptyMap())
data class HealthConnectSession(val sessionId: String, val startTime: String, val endTime: String, val segments: List<HealthConnectSegment>, val notes: String? = null)

@kotlinx.serialization.Serializable
data class HealthInteropLoss(val path: String, val reason: String, val destination: String)

@kotlinx.serialization.Serializable
data class HealthInteropEnvelope(
    val interopVersion: String = "0.1.0",
    val target: String,
    val recordId: String,
    val canonicalWorkout: JsonObject? = null,
    val projection: JsonObject,
    val fidelity: String = "lossless_with_sidecar",
    val losses: List<HealthInteropLoss> = emptyList(),
    val warnings: List<String> = listOf("Persist canonicalWorkout with the native record; target APIs do not represent every DB++ field.")
)

/**
 * Platform-neutral, lossless envelope. An Android host can turn projection
 * into ExerciseSessionRecord/ExerciseSegment using the Health Connect SDK;
 * the JVM artifact intentionally does not depend on Android classes.
 */
fun Workout.toHealthInteropEnvelope(target: String = "health-connect", json: Json = Json { encodeDefaults = true }): HealthInteropEnvelope {
    require(target in setOf("health-connect", "healthkit", "garmin-fit")) { "unsupported health interop target: $target" }
    val canonical = json.encodeToJsonElement(this).jsonObject
    val segments = buildList {
        exercises.forEach { observation ->
            observation.sets.forEachIndexed { index, set ->
                add(buildJsonObject {
                    put("exerciseType", JsonPrimitive("strength_training"))
                    observation.exerciseId?.let { put("exerciseId", JsonPrimitive(it)) }
                    observation.exerciseName?.let { put("exerciseName", JsonPrimitive(it)) }
                    put("startTime", JsonPrimitive(startTime))
                    put("endTime", JsonPrimitive(endTime ?: startTime))
                    set.reps?.let { put("repetitions", JsonPrimitive(it)) }
                    set.load?.takeIf { it.unit == "kg" }?.let { put("weightKg", JsonPrimitive(it.value)) }
                    set.rpe?.let { put("rateOfPerceivedExertion", JsonPrimitive(it)) }
                    put("setIndex", JsonPrimitive(set.setNumber ?: index + 1))
                })
            }
        }
    }
    val projection = buildJsonObject {
        put("startTime", JsonPrimitive(startTime))
        put("endTime", JsonPrimitive(endTime ?: startTime))
        put("exerciseType", JsonPrimitive("strength_training"))
        put("metadata", buildJsonObject {
            put("clientRecordId", JsonPrimitive(sessionId))
            put("clientRecordVersion", JsonPrimitive(1))
            put("org.free-exercise-db-plusplus.canonicalWorkoutJSON", JsonPrimitive(json.encodeToString(JsonObject.serializer(), canonical)))
        })
        put("segments", kotlinx.serialization.json.JsonArray(segments))
    }
    return HealthInteropEnvelope(target = target, recordId = sessionId, canonicalWorkout = canonical, projection = projection)
}

fun HealthInteropEnvelope.toWorkout(json: Json = Json { ignoreUnknownKeys = true }): Workout {
    val canonical = canonicalWorkout ?: throw ValidationException("health interop envelope has no DB++ sidecar")
    return json.decodeFromJsonElement(Workout.serializer(), canonical)
}

/** Platform-neutral projection; an Android app can map this to ExerciseSessionRecord/ExerciseSegment. */
fun Workout.toHealthConnect(): HealthConnectSession {
    val end = endTime ?: throw ValidationException("Health Connect requires endTime")
    val segments = exercises.flatMap { observation ->
        val id = observation.exerciseId ?: return@flatMap emptyList()
        observation.sets.map { set ->
            val extensions = mapOf("dbpp.laterality" to (observation.laterality ?: "unspecified"))
            HealthConnectSegment(id, observation.exerciseName, set.reps, set.load?.takeIf { it.unit == "kg" }?.value, set.setNumber ?: 1, MappingQuality.EXTENSION_REQUIRED, extensions)
        }
    }
    return HealthConnectSession(sessionId, startTime, end, segments, notes)
}
