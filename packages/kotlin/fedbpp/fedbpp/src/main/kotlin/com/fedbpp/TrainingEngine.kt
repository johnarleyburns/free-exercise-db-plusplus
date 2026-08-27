package com.fedbpp

import kotlinx.serialization.json.JsonElement

/** Offline native-engine façade.  No Python bridge, subprocess, or network. */
class TrainingEngine(val database: Database, val relationships: ExerciseRelationships? = null) {
    fun validateWorkoutIntent(intent: WorkoutIntent): List<String> =
        com.fedbpp.validateWorkoutIntent(intent, database, relationships)

    fun resolveIntent(intent: WorkoutIntent, profile: JsonElement? = null, target: JsonElement? = null, history: JsonElement? = null, asOf: String? = null): IntentResolutionResult =
        com.fedbpp.resolveIntent(intent, database, profile, target, relationships, history, asOf)

    fun evaluatePlan(plan: JsonElement, profile: JsonElement? = null, target: JsonElement? = null): JsonElement =
        com.fedbpp.evaluatePlan(plan, database, profile, target, relationships)

    fun generatePlan(profile: JsonElement, target: JsonElement, requiredExerciseIds: List<String> = emptyList()): JsonElement =
        com.fedbpp.generatePlan(profile, target, database, relationships, requiredExerciseIds)

    fun deriveTrainingState(history: JsonElement, asOf: String): JsonElement =
        com.fedbpp.deriveTrainingState(history, asOf)
}
