package com.fedbpp

import java.io.File
import java.io.InputStream
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.contentOrNull

class ValidationException(message: String): IllegalArgumentException(message)
class ExerciseNotFoundException(id: String): NoSuchElementException("Exercise not found: $id")

internal val fedbppJson = Json { ignoreUnknownKeys = true; explicitNulls = false; encodeDefaults = true }

class Database private constructor(private val document: DatabaseDocument) {
    val metadata get() = document.metadata
    val size get() = document.exercises.size
    val exerciseIds get() = document.exercises.keys.toSet()
    val equipmentVocabulary get() = document.exercises.values.mapNotNull { it.source["equipment"]?.jsonPrimitive?.contentOrNull }.toSet()
    fun getExercise(id: String): Exercise = document.exercises[id] ?: throw ExerciseNotFoundException(id)
    fun findExercises(query: String): List<Exercise> = document.exercises.values.filter { it.exerciseId.contains(query, ignoreCase = true) }.sortedBy { it.exerciseId }
    fun exercisesForMuscle(muscle: String): List<Exercise> = document.exercises.values.filter { muscle in it.annotation.direct || muscle in it.annotation.indirect }.sortedBy { it.exerciseId }
    companion object {
        fun load(file: File): Database = file.inputStream().use(::load)
        fun load(input: InputStream): Database = try { Database(fedbppJson.decodeFromString(DatabaseDocument.serializer(), input.reader().readText())) } catch (e: Exception) { throw ValidationException("Unable to decode database: ${e.message}") }
    }
}

fun loadRelationships(file: File): ExerciseRelationships = file.inputStream().use { input ->
    try { fedbppJson.decodeFromString(ExerciseRelationships.serializer(), input.reader().readText()) }
    catch (e: Exception) { throw ValidationException("Unable to decode relationships: ${e.message}") }
}
fun ExerciseRelationships.familyFor(exerciseId: String): ExerciseFamily? = relationships.firstOrNull { it.sourceExerciseId == exerciseId && it.relationship == "member_of_family" }?.let { families[it.familyId] }
fun ExerciseRelationships.members(familyId: String): List<String> = relationships.filter { it.familyId == familyId && it.relationship == "member_of_family" }.map { it.sourceExerciseId }.sorted()

fun Workout.validate() {
    if (schemaVersion != "0.2.0") throw ValidationException("unsupported workout schema: $schemaVersion")
    if (sessionId.isBlank()) throw ValidationException("sessionId must not be blank")
    if (startTime.isBlank()) throw ValidationException("startTime must not be blank")
    exercises.forEach { observation ->
        if (observation.exerciseId.isNullOrBlank() && observation.exerciseName.isNullOrBlank()) throw ValidationException("exercise observation requires exerciseId or exerciseName")
        if (observation.order < 1) throw ValidationException("exercise order must be positive")
        observation.sets.forEach { if (it.setNumber < 1) throw ValidationException("setNumber must be positive") }
    }
}

fun Workout.Companion.load(file: File, validate: Boolean = true): Workout = file.inputStream().use { load(it, validate) }
fun Workout.Companion.load(input: InputStream, validate: Boolean = true): Workout = fedbppJson.decodeFromString(Workout.serializer(), input.reader().readText()).also { if (validate) it.validate() }

fun Workout.migrate(): Workout {
    if (schemaVersion == "0.2.0") return this
    if (!schemaVersion.startsWith("0.1.")) throw ValidationException("unsupported workout schema: $schemaVersion")
    return copy(schemaVersion = "0.2.0", exercises = exercises.map { it.copy(laterality = if (it.laterality == "unspecified") "unspecified" else it.laterality) })
}

fun Workout.effectiveSets(database: Database): Map<String, Double> {
    val totals = mutableMapOf<String, Double>()
    exercises.forEach { observation ->
        val exercise = observation.exerciseId?.let { runCatching { database.getExercise(it) }.getOrNull() } ?: return@forEach
        if (!exercise.annotation.volumeEligible) return@forEach
        val countedTypes = setOf("working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted")
        val sets = observation.sets.count { it.completed && it.setType in countedTypes }.toDouble()
        val credits = database.metadata["setCredits"]?.jsonObject
        fun credit(role: String, fallback: Double) = credits?.get(role)?.jsonPrimitive?.doubleOrNull ?: fallback
        exercise.annotation.direct.forEach { totals[it] = (totals[it] ?: 0.0) + sets * credit("direct", 1.0) }
        exercise.annotation.indirect.forEach { totals[it] = (totals[it] ?: 0.0) + sets * credit("indirect", 0.5) }
        exercise.annotation.stabilizers.forEach { totals[it] = (totals[it] ?: 0.0) + sets * credit("stabilizer", 0.0) }
    }
    return totals.toSortedMap()
}
