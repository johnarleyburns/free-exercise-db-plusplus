package com.fedbpp

import java.time.Instant
import kotlinx.serialization.Serializable
import kotlinx.serialization.EncodeDefault
import kotlinx.serialization.EncodeDefault.Mode.ALWAYS
import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.contentOrNull

@Serializable
enum class TrainingOperation {
    @kotlinx.serialization.SerialName("resolve_intent") RESOLVE_INTENT,
    @kotlinx.serialization.SerialName("generate_from_intent") GENERATE_FROM_INTENT,
    @kotlinx.serialization.SerialName("generate_plan") GENERATE_PLAN,
    @kotlinx.serialization.SerialName("evaluate_plan") EVALUATE_PLAN,
    @kotlinx.serialization.SerialName("derive_state") DERIVE_STATE,
    @kotlinx.serialization.SerialName("suggest_progression") SUGGEST_PROGRESSION,
    @kotlinx.serialization.SerialName("adapt_plan") ADAPT_PLAN
}

@Serializable
data class TrainingRequest(
    val schemaVersion: String = "0.1.0",
    val requestId: String,
    val operation: TrainingOperation,
    val intent: WorkoutIntent? = null,
    val profile: TrainingProfile? = null,
    val target: VolumeTarget? = null,
    val history: TrainingHistory? = null,
    val trainingState: TrainingState? = null,
    val currentPlan: WorkoutPlan? = null,
    val plan: WorkoutPlan? = null,
    val asOf: String? = null,
    @Serializable(with = ApplicationHistoryWindowSerializer::class)
    val historyWindow: TrainingHistoryWindow? = null,
    val options: JsonObject = JsonObject(emptyMap())
)

private object ApplicationHistoryWindowSerializer : KSerializer<TrainingHistoryWindow> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("TrainingHistoryWindow", PrimitiveKind.STRING)
    override fun serialize(encoder: Encoder, value: TrainingHistoryWindow) {
        if (value is TrainingHistoryWindow.Custom) {
            (encoder as JsonEncoder).encodeJsonElement(buildJsonObject {
                put("start", value.start); put("end", value.end)
            })
        } else encoder.encodeString(value.name())
    }
    override fun deserialize(decoder: Decoder): TrainingHistoryWindow {
        val value = (decoder as JsonDecoder).decodeJsonElement()
        if (value is JsonObject) return TrainingHistoryWindow.Custom(
            value["start"]?.jsonPrimitive?.content ?: error("custom window start is required"),
            value["end"]?.jsonPrimitive?.content ?: error("custom window end is required"))
        return when (val name = value.jsonPrimitive.content) {
            "last_7_days" -> TrainingHistoryWindow.Last7Days
            "last_28_days" -> TrainingHistoryWindow.Last28Days
            "current_plan_cycle" -> TrainingHistoryWindow.CurrentPlanCycle
            "current_phase" -> TrainingHistoryWindow.CurrentPhase
            else -> error("unsupported application history window: $name")
        }
    }
    private fun TrainingHistoryWindow.name() = when (this) {
        TrainingHistoryWindow.Last7Days -> "last_7_days"
        TrainingHistoryWindow.Last28Days -> "last_28_days"
        TrainingHistoryWindow.CurrentPlanCycle -> "current_plan_cycle"
        TrainingHistoryWindow.CurrentPhase -> "current_phase"
        is TrainingHistoryWindow.Custom -> "custom_date_range"
    }
}

@OptIn(kotlinx.serialization.ExperimentalSerializationApi::class)
@Serializable
data class TrainingResult(
    @EncodeDefault(ALWAYS)
    val schemaVersion: String = "0.1.0",
    val requestId: String,
    val operation: TrainingOperation,
    val status: String,
    @EncodeDefault(ALWAYS) val resolution: IntentResolutionResult? = null,
    @EncodeDefault(ALWAYS) val plan: WorkoutPlan? = null,
    @EncodeDefault(ALWAYS) val evaluation: PlanEvaluation? = null,
    @EncodeDefault(ALWAYS) val trainingState: TrainingState? = null,
    @EncodeDefault(ALWAYS)
    val coachDecisions: List<CoachDecision> = emptyList(),
    @EncodeDefault(ALWAYS) val adaptation: AdaptivePlanResult? = null,
    @EncodeDefault(ALWAYS)
    val missingInformation: List<MissingInformation> = emptyList(),
    @EncodeDefault(ALWAYS)
    val conflicts: List<IntentConflict> = emptyList(),
    @EncodeDefault(ALWAYS)
    val warnings: List<String> = emptyList(),
    @EncodeDefault(ALWAYS)
    val issues: List<JsonElement> = emptyList(),
    @EncodeDefault(ALWAYS)
    val provenance: Map<String, JsonElement> = emptyMap()
)

private fun JsonObject.text(name: String): String? = (this[name] as? JsonPrimitive)?.contentOrNull
private fun JsonObject.texts(name: String): List<String> =
    (this[name] as? JsonArray)?.mapNotNull { (it as? JsonPrimitive)?.contentOrNull } ?: emptyList()

private fun List<PlanIssue>.asApplicationIssues(): List<JsonElement> =
    map { apiJson.encodeToJsonElement(PlanIssue.serializer(), it) }

private fun invalidResult(request: TrainingRequest, code: String) = TrainingResult(
    requestId = request.requestId, operation = request.operation, status = "invalid",
    issues = listOf(buildJsonObject { put("code", code) })
)

/** Explicit application orchestration over the existing canonical operations. */
fun TrainingEngine.processTrainingRequest(request: TrainingRequest): TrainingResult {
    if (request.schemaVersion != "0.1.0" || request.requestId.isBlank()) return invalidResult(request, "INVALID_REQUEST")
    when (request.operation) {
        TrainingOperation.RESOLVE_INTENT -> {
            val intent = request.intent ?: return invalidResult(request, "MISSING_INTENT")
            val result = resolveIntent(intent, request.profile, request.target, request.history, request.asOf?.let(Instant::parse))
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = result.status,
                resolution = result, missingInformation = result.missingInformation,
                conflicts = result.conflicts, warnings = result.warnings, provenance = result.provenance)
        }
        TrainingOperation.GENERATE_FROM_INTENT -> {
            val intent = request.intent ?: return invalidResult(request, "MISSING_INTENT")
            val result = generatePlanFromIntent(intent, request.profile, request.target, request.history,
                request.currentPlan, request.asOf?.let(Instant::parse))
            val generation = result.generation ?: return TrainingResult(requestId = request.requestId,
                operation = request.operation, status = result.resolution.status, resolution = result.resolution,
                missingInformation = result.resolution.missingInformation, conflicts = result.resolution.conflicts,
                warnings = result.resolution.warnings, provenance = result.resolution.provenance)
            val issues = generation.unsatisfiedConstraints + generation.unsatisfiedTargets + generation.unsatisfiedSoftPreferences
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = generation.status,
                resolution = result.resolution, plan = generation.plan, evaluation = generation.evaluation,
                issues = issues.asApplicationIssues(), warnings = result.resolution.warnings, provenance = generation.provenance)
        }
        TrainingOperation.GENERATE_PLAN -> {
            val profile = request.profile ?: return invalidResult(request, "MISSING_PROFILE_OR_TARGET")
            val target = request.target ?: return invalidResult(request, "MISSING_PROFILE_OR_TARGET")
            val policy = request.options.text("policy") ?: "full-body-general-v1"
            val generation = generatePlan(PlanGenerationRequest(profile = profile, target = target, policy = policy,
                trainingState = request.trainingState, currentPlan = request.currentPlan,
                requiredExerciseIds = request.options.texts("requiredExerciseIds"),
                lockedExerciseIds = request.options.texts("lockedExerciseIds"),
                requiredFamilyIds = request.options.texts("requiredFamilyIds"),
                additionalExclusions = request.options.texts("additionalExclusions")))
            val issues = generation.unsatisfiedConstraints + generation.unsatisfiedTargets + generation.unsatisfiedSoftPreferences
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = generation.status,
                plan = generation.plan, evaluation = generation.evaluation, issues = issues.asApplicationIssues(), provenance = generation.provenance)
        }
        TrainingOperation.EVALUATE_PLAN -> {
            val plan = request.plan ?: return invalidResult(request, "MISSING_PLAN")
            val evaluation = evaluatePlan(plan, request.profile, request.target)
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = "evaluated",
                plan = plan, evaluation = evaluation, warnings = evaluation.warnings,
                issues = evaluation.toJson()["constraints"]?.jsonObject?.get("violations")?.jsonArray ?: emptyList(),
                provenance = evaluation.provenance)
        }
        TrainingOperation.DERIVE_STATE -> {
            val history = request.history ?: return invalidResult(request, "MISSING_HISTORY_OR_AS_OF")
            val asOf = request.asOf?.let { runCatching { Instant.parse(it) }.getOrNull() }
                ?: return invalidResult(request, "MISSING_HISTORY_OR_AS_OF")
            val historyJson = buildJsonObject {
                apiJson.encodeToJsonElement(TrainingHistory.serializer(), history).jsonObject.forEach { (key, value) -> put(key, value) }
                request.options["timezone"]?.let { put("timezone", it) }
            }
            val state = TrainingState.fromJson(deriveTrainingStateCanonical(
                historyJson, asOf,
                request.historyWindow ?: TrainingHistoryWindow.Last28Days, database, relationships,
                request.target?.let { apiJson.encodeToJsonElement(VolumeTarget.serializer(), it) },
                canonicalAsOf = request.asOf))
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = "state_derived",
                trainingState = state, provenance = state.provenance)
        }
        TrainingOperation.SUGGEST_PROGRESSION -> {
            val plan = request.plan ?: return invalidResult(request, "MISSING_PLAN_OR_TRAINING_STATE")
            val state = request.trainingState ?: return invalidResult(request, "MISSING_PLAN_OR_TRAINING_STATE")
            val decisions = suggestProgression(plan, state, request.options.text("policy") ?: "double-progression-v1")
            return TrainingResult(requestId = request.requestId, operation = request.operation,
                status = if (decisions.isEmpty()) "insufficient_data" else "progression_available",
                plan = plan, coachDecisions = decisions)
        }
        TrainingOperation.ADAPT_PLAN -> {
            val profile = request.profile ?: return invalidResult(request, "MISSING_ADAPTATION_INPUT")
            val target = request.target ?: return invalidResult(request, "MISSING_ADAPTATION_INPUT")
            val current = request.currentPlan ?: return invalidResult(request, "MISSING_ADAPTATION_INPUT")
            val history = request.history ?: return invalidResult(request, "MISSING_ADAPTATION_INPUT")
            val asOf = request.asOf?.let { runCatching { Instant.parse(it) }.getOrNull() }
                ?: return invalidResult(request, "MISSING_ADAPTATION_INPUT")
            val planningPolicy = request.options.text("planningPolicy")
                ?: if (evaluatePlan(current, profile, target).summary.satisfiesHardConstraints) null else "full-body-general-v1"
            val adapted = adaptPlan(PlanAdaptationRequest(profile, target, current, history, request.trainingState,
                asOf, request.options.text("policy") ?: "general-adaptive-v1",
                planningPolicy))
            return TrainingResult(requestId = request.requestId, operation = request.operation, status = adapted.status,
                plan = adapted.currentPlan, trainingState = adapted.trainingState, coachDecisions = adapted.decisions,
                adaptation = adapted, issues = adapted.unresolvedIssues.asApplicationIssues(), provenance = adapted.provenance)
        }
    }
}
