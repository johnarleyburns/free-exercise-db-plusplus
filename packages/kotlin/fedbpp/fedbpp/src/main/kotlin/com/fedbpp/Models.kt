package com.fedbpp

import kotlinx.serialization.Serializable

@Serializable data class ExerciseAnnotation(
    val direct: List<String> = emptyList(), val indirect: List<String> = emptyList(),
    val stabilizers: List<String> = emptyList(), val volumeEligible: Boolean = false,
    val confidence: String? = null, val patterns: List<String> = emptyList()
)
@Serializable data class Exercise(val exerciseId: String, val annotation: ExerciseAnnotation = ExerciseAnnotation(), val source: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap())
@Serializable internal data class DatabaseDocument(val metadata: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap(), val exercises: Map<String, Exercise> = emptyMap())
@Serializable data class ExerciseFamily(val familyId: String, val name: String, val aliases: List<String> = emptyList())
@Serializable data class ExerciseRelationship(val sourceExerciseId: String, val targetExerciseId: String? = null, val familyId: String, val relationship: String, val dimensions: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap(), val confidence: String)
@Serializable data class ExerciseRelationships(val schemaVersion: String, val families: Map<String, ExerciseFamily>, val relationships: List<ExerciseRelationship>)

@Serializable data class Quantity(val value: Double, val unit: String)
@Serializable data class SetObservation(
    val setNumber: Int, val setType: String, val reps: Int? = null, val load: Quantity? = null,
    val duration: Quantity? = null, val distance: Quantity? = null, val rpe: Double? = null,
    val rir: Double? = null, val completed: Boolean, val laterality: String? = null
)
@Serializable data class ExerciseObservation(
    val exerciseId: String? = null, val exerciseName: String? = null, val order: Int,
    val laterality: String = "unspecified", val sets: List<SetObservation> = emptyList()
)
@Serializable data class Workout(
    val schemaVersion: String, val sessionId: String, val startTime: String,
    val endTime: String? = null, val athleteId: String? = null,
    val notes: String? = null, val exercises: List<ExerciseObservation> = emptyList()
) { companion object }
