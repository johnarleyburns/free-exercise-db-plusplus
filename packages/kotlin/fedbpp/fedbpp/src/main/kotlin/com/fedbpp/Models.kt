package com.fedbpp

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.contentOrNull
import java.util.Locale

@Serializable data class ExerciseAnnotation(
    val direct: List<String> = emptyList(), val indirect: List<String> = emptyList(),
    val stabilizers: List<String> = emptyList(), val volumeEligible: Boolean = false,
    val confidence: String? = null, val patterns: List<String> = emptyList()
)
@Serializable data class LocalizedExerciseName(
    val preferred: String,
    val aliases: List<String> = emptyList(),
    val searchOnly: List<String> = emptyList(),
    val region: String? = null,
    val sourceRefs: List<String> = emptyList(),
    val reviewStatus: String = "provisional"
)
@Serializable data class Exercise(
    val exerciseId: String,
    val annotation: ExerciseAnnotation = ExerciseAnnotation(),
    val source: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap(),
    val localizedNames: Map<String, LocalizedExerciseName> = emptyMap()
) {
    private fun localeCandidates(locale: Locale): List<String> {
        val requested = locale.toLanguageTag()
        val scriptLocale = if (locale.language == "zh") {
            when (locale.script) {
                "Hans" -> "zh-Hans"
                "Hant" -> "zh-Hant"
                else -> when (locale.country) {
                    "CN", "SG", "MY" -> "zh-Hans"
                    "TW", "HK", "MO" -> "zh-Hant"
                    else -> null
                }
            }
        } else null
        return listOfNotNull(requested, scriptLocale, locale.language.takeIf { it.isNotBlank() }, "en").distinct()
    }
    fun localizedName(locale: Locale = Locale.getDefault()): LocalizedExerciseName? =
        localeCandidates(locale).firstNotNullOfOrNull { localizedNames[it] }
    fun preferredName(locale: Locale = Locale.getDefault()): String =
        localizedName(locale)?.preferred ?: source["name"]?.jsonPrimitive?.contentOrNull ?: exerciseId
    fun aliases(locale: Locale = Locale.getDefault()): List<String> =
        localizedName(locale)?.let { it.aliases + it.searchOnly } ?: emptyList()
}
@Serializable internal data class DatabaseDocument(val metadata: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap(), val exercises: Map<String, Exercise> = emptyMap())
@Serializable data class ExerciseFamily(val familyId: String, val name: String, val aliases: List<String> = emptyList())
@Serializable data class ExerciseRelationship(val sourceExerciseId: String, val targetExerciseId: String? = null, val familyId: String, val relationship: String, val dimensions: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap(), val confidence: String)
@Serializable data class ExerciseRelationships(val schemaVersion: String, val families: Map<String, ExerciseFamily>, val relationships: List<ExerciseRelationship>)

@Serializable data class Quantity(val value: Double, val unit: String)
@Serializable data class SetObservation(
    val setNumber: Int? = null, val setType: String = "working", val reps: Int? = null, val load: Quantity? = null,
    val duration: Quantity? = null, val distance: Quantity? = null, val rpe: Double? = null,
    val rir: Double? = null, val completed: Boolean = false, val laterality: String? = null,
    val setPrescriptionId: String? = null, val notes: String? = null,
    val extensions: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap()
)
@Serializable data class ExerciseObservation(
    val exerciseId: String? = null, val exerciseName: String? = null, val order: Int = 1,
    val laterality: String = "unspecified", val sets: List<SetObservation> = emptyList(),
    val exercisePrescriptionId: String? = null, val substitutionOfPrescriptionId: String? = null,
    val substitutionReason: String? = null, val notes: String? = null,
    val substitution: kotlinx.serialization.json.JsonElement? = null,
    val extensions: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap()
)
@Serializable data class Workout(
    val schemaVersion: String, val sessionId: String, val startTime: String,
    val endTime: String? = null, val athleteId: String? = null,
    val notes: String? = null, val exercises: List<ExerciseObservation> = emptyList(),
    val programId: String? = null, val programDayId: String? = null,
    val coachId: String? = null, val timezone: String? = null, val location: String? = null,
    val tags: List<String>? = null, val planReference: PlanReference? = null,
    val source: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    val extensions: Map<String, kotlinx.serialization.json.JsonElement> = emptyMap()
) { companion object }

@Serializable data class PlanReference(
    val planId: String? = null, val revisionId: String? = null,
    val planSessionId: String? = null, val occurrenceId: String? = null
)
