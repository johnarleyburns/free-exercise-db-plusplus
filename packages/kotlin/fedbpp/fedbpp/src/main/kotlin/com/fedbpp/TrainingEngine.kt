package com.fedbpp

import java.time.Instant
import kotlinx.serialization.json.*

/** Single application-facing entry point for the offline JVM engine. */
class TrainingEngine(val database: Database, val relationships: ExerciseRelationships? = null) {
    companion object { fun bundled(): TrainingEngine = TrainingEngine(Database.bundled(), bundledRelationships()) }
    fun validateIntent(intent: WorkoutIntent): IntentValidationResult {
        val errors = com.fedbpp.validateWorkoutIntent(intent, database, relationships)
        return IntentValidationResult(if (errors.isEmpty()) "valid" else "invalid", errors.map { IntentValidationIssue("INVALID_INTENT", message = it) })
    }
    fun validateWorkoutIntent(intent: WorkoutIntent): List<String> = com.fedbpp.validateWorkoutIntent(intent, database, relationships)
    fun resolveIntent(intent: WorkoutIntent, profile: TrainingProfile? = null, target: VolumeTarget? = null, history: TrainingHistory? = null, asOf: Instant? = null): IntentResolutionResult =
        com.fedbpp.resolveIntent(intent, database, profile?.let { apiJson.encodeToJsonElement(TrainingProfile.serializer(), it) }, target?.let { apiJson.encodeToJsonElement(VolumeTarget.serializer(), it) }, relationships, history?.let { apiJson.encodeToJsonElement(TrainingHistory.serializer(), it) }, asOf?.toString())
    fun resolveIntentJson(intent: WorkoutIntent, profile: JsonElement? = null, target: JsonElement? = null, history: JsonElement? = null, asOf: String? = null): IntentResolutionResult =
        com.fedbpp.resolveIntent(intent, database, profile, target, relationships, history, asOf)
    fun generatePlan(request: PlanGenerationRequest): GeneratedPlanResult {
        val profile = apiJson.encodeToJsonElement(TrainingProfile.serializer(), request.profile)
        val target = apiJson.encodeToJsonElement(VolumeTarget.serializer(), request.target)
        val options = buildJsonObject {
            put("policy", request.policy)
            request.currentPlan?.let { put("currentPlan", it.toJson()) }
            request.trainingState?.let { put("trainingState", apiJson.encodeToJsonElement(TrainingState.serializer(), it)) }
            put("lockedExerciseIds", JsonArray(request.lockedExerciseIds.distinct().sorted().map(::JsonPrimitive)))
            put("additionalExclusions", JsonArray(request.additionalExclusions.distinct().sorted().map(::JsonPrimitive)))
            put("requiredFamilyIds", JsonArray(request.requiredFamilyIds.distinct().sorted().map(::JsonPrimitive)))
        }
        return decodeGenerated(com.fedbpp.generatePlan(profile, target, database, relationships, (request.requiredExerciseIds + request.lockedExerciseIds).distinct(), options))
    }
    fun generatePlanFromIntent(intent: WorkoutIntent, profile: TrainingProfile? = null, target: VolumeTarget? = null, history: TrainingHistory? = null, currentPlan: WorkoutPlan? = null, asOf: Instant? = null): IntentPlanResult {
        val resolution = resolveIntent(intent, profile, target, history, asOf)
        if (resolution.status !in setOf("resolved", "resolved_with_defaults")) return IntentPlanResult(resolution)
        val ids = (intent.exerciseConstraints?.requiredExerciseIds.orEmpty() + intent.exerciseConstraints?.lockedExerciseIds.orEmpty()).distinct()
        val raw = com.fedbpp.generatePlan(resolution.resolvedProfile!!, resolution.resolvedTarget!!, database, relationships, ids, buildJsonObject {
            currentPlan?.let { put("currentPlan", it.toJson()) }
            intent.exerciseConstraints?.lockedExerciseIds?.let { put("lockedExerciseIds", JsonArray(it.distinct().sorted().map(::JsonPrimitive))) }
            intent.exerciseConstraints?.excludedExerciseIds?.let { put("additionalExclusions", JsonArray(it.distinct().sorted().map(::JsonPrimitive))) }
            intent.exerciseConstraints?.excludedFamilyIds?.let { put("excludedFamilyIds", JsonArray(it.distinct().sorted().map(::JsonPrimitive))) }
        })
        return IntentPlanResult(resolution, decodeGenerated(raw))
    }
    fun evaluatePlan(plan: WorkoutPlan, profile: TrainingProfile? = null, target: VolumeTarget? = null): PlanEvaluation =
        PlanEvaluation.fromJson(com.fedbpp.evaluatePlan(plan.toJson(), database, profile?.let { apiJson.encodeToJsonElement(TrainingProfile.serializer(), it) }, target?.let { apiJson.encodeToJsonElement(VolumeTarget.serializer(), it) }, relationships))
    fun evaluatePlanJson(plan: JsonElement, profile: JsonElement? = null, target: JsonElement? = null): JsonElement = com.fedbpp.evaluatePlan(plan, database, profile, target, relationships)
    fun deriveTrainingState(history: TrainingHistory, asOf: Instant, window: TrainingHistoryWindow = TrainingHistoryWindow.Last28Days, target: VolumeTarget? = null): TrainingState =
        TrainingState.fromJson(deriveTrainingStateCanonical(apiJson.encodeToJsonElement(TrainingHistory.serializer(), history), asOf, window, database, relationships, target?.let { apiJson.encodeToJsonElement(VolumeTarget.serializer(), it) }))
    fun deriveTrainingStateJson(history: JsonElement, asOf: Instant, window: TrainingHistoryWindow = TrainingHistoryWindow.Last28Days, target: JsonElement? = null): JsonElement =
        deriveTrainingStateCanonical(history, asOf, window, database, relationships, target)
    fun suggestProgression(plan: WorkoutPlan, trainingState: TrainingState, policy: String = "double-progression-v1", parameters: JsonElement? = null): List<CoachDecision> =
        com.fedbpp.suggestProgression(plan.toJson(), apiJson.encodeToJsonElement(TrainingState.serializer(), trainingState), policy, parameters).map { apiJson.decodeFromJsonElement(CoachDecision.serializer(), it) }
    fun adaptPlan(request: PlanAdaptationRequest): AdaptivePlanResult = decodeAdaptive(adaptPlanCanonical(request, database, relationships))
    private fun decodeGenerated(raw: JsonElement): GeneratedPlanResult {
        val x = raw.jsonObject
        return GeneratedPlanResult(x["status"]?.jsonPrimitive?.content ?: "invalid_input", x["plan"]?.takeUnless { it is JsonNull }?.let(WorkoutPlan::fromJson), x["evaluation"]?.takeUnless { it is JsonNull }?.let(PlanEvaluation::fromJson), x["policy"], x["unsatisfiedConstraints"].jsonArrayOrEmpty().mapNotNull { runCatching { apiJson.decodeFromJsonElement(PlanIssue.serializer(), it) }.getOrNull() }, x["unsatisfiedTargets"].jsonArrayOrEmpty().mapNotNull { runCatching { apiJson.decodeFromJsonElement(PlanIssue.serializer(), it) }.getOrNull() }, x["unsatisfiedSoftPreferences"].jsonArrayOrEmpty().mapNotNull { runCatching { apiJson.decodeFromJsonElement(PlanIssue.serializer(), it) }.getOrNull() }, x["provenance"].jsonObjectOrEmpty)
    }
    private fun decodeAdaptive(raw: JsonElement): AdaptivePlanResult = apiJson.decodeFromJsonElement(AdaptivePlanResult.serializer(), raw)
}
private val JsonElement?.jsonObjectOrEmpty get() = this as? JsonObject ?: JsonObject(emptyMap())
private fun JsonElement?.jsonArrayOrEmpty() = this as? JsonArray ?: JsonArray(emptyList())
