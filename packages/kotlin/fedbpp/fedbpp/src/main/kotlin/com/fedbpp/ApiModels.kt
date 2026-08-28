package com.fedbpp

import java.time.Instant
import kotlinx.serialization.*
import kotlinx.serialization.descriptors.*
import kotlinx.serialization.encoding.*
import kotlinx.serialization.json.*

@Serializable(with = TargetRangeSerializer::class)
data class TargetRange(val min: Double? = null, val target: Double? = null, val max: Double? = null)

object TargetRangeSerializer : KSerializer<TargetRange> {
    override val descriptor: SerialDescriptor = JsonElement.serializer().descriptor
    override fun serialize(encoder: Encoder, value: TargetRange) {
        val out = buildJsonObject {
            value.min?.let { put("min", it) }; value.target?.let { put("target", it) }; value.max?.let { put("max", it) }
        }
        (encoder as? JsonEncoder)?.encodeJsonElement(out) ?: error("TargetRange requires JSON")
    }
    override fun deserialize(decoder: Decoder): TargetRange {
        val value = (decoder as? JsonDecoder)?.decodeJsonElement() ?: error("TargetRange requires JSON")
        if (value is JsonPrimitive) return TargetRange(target = value.doubleOrNull)
        val fields = value as? JsonObject ?: return TargetRange()
        fun number(vararg keys: String) = keys.firstNotNullOfOrNull { fields[it]?.jsonPrimitive?.doubleOrNull }
        return TargetRange(number("min", "minimumSets"), number("target", "targetSets"), number("max", "maximumSets"))
    }
}
@Serializable data class TrainingGoal(val type: String, val priority: Int? = null)
@Serializable data class ProfileConstraints(val excludedExerciseIds: List<String> = emptyList(), val excludedFamilyIds: List<String> = emptyList())
@Serializable data class Availability(val cycleLengthDays: Int? = null, val sessionsPerCycle: TargetRange? = null, val minutesPerSession: TargetRange? = null, val exercisesPerSession: TargetRange? = null, val preferredDayOffsets: List<Int> = emptyList(), val excludedDayOffsets: List<Int> = emptyList())
@Serializable data class TrainingProfile(val schemaVersion: String = "0.1.0", val profileId: String? = null, val subjectId: String? = null, val goals: List<TrainingGoal> = emptyList(), val experience: String? = null, val availability: Availability? = null, val equipment: List<String> = emptyList(), val exercisePreferences: WorkoutPreferences = WorkoutPreferences(), val constraints: ProfileConstraints = ProfileConstraints(), val extensions: Map<String, JsonElement> = emptyMap())
@Serializable data class VolumeTarget(val schemaVersion: String = "0.1.0", val targetId: String, val periodDays: Int, val muscles: Map<String, TargetRange> = emptyMap(), val frequency: Map<String, Map<String, TargetRange>> = emptyMap(), val movementPatterns: Map<String, TargetRange> = emptyMap(), val families: Map<String, TargetRange> = emptyMap(), val provenance: JsonElement? = null)

@Serializable data class SetPrescription(val setPrescriptionId: String? = null, val setType: String = "working", val reps: TargetRange? = null, val load: JsonElement? = null, val effort: JsonElement? = null, val volumeEligible: Boolean? = null, val extensions: Map<String, JsonElement> = emptyMap())

@Serializable(with = WorkoutPlanSerializer::class)
class WorkoutPlan internal constructor(internal val document: JsonObject) {
    val schemaVersion get() = document["schemaVersion"]?.jsonPrimitive?.content ?: "0.1.0"
    val planId get() = document["planId"]?.jsonPrimitive?.contentOrNull
    val revisionId get() = document["revisionId"]?.jsonPrimitive?.contentOrNull
    val name get() = document["name"]?.jsonPrimitive?.contentOrNull
    val cycleLengthDays get() = document["cycle"]?.jsonObject?.get("lengthDays")?.jsonPrimitive?.intOrNull
    val sessions get() = document["sessions"]?.jsonArray?.map { PlanSession(it.jsonObject) } ?: emptyList()
    fun toJson(): JsonObject = document
    override fun equals(other: Any?) = other is WorkoutPlan && document == other.document
    override fun hashCode() = document.hashCode()
    override fun toString() = document.toString()
    companion object {
        fun fromJson(value: JsonElement) = WorkoutPlan(value.jsonObject)
        fun create(planId: String, revisionId: String, name: String, cycleLengthDays: Int, sessions: List<PlanSession>) = WorkoutPlan(buildJsonObject { put("schemaVersion", "0.2.0"); put("planId", planId); put("revisionId", revisionId); put("name", name); put("cycle", buildJsonObject { put("lengthDays", cycleLengthDays) }); put("sessions", buildJsonArray { sessions.forEach { add(it.toJson()) } }) })
    }
}
class PlanSession internal constructor(internal val document: JsonObject) {
    val planSessionId get() = document["planSessionId"]?.jsonPrimitive?.contentOrNull
    val dayOffset get() = document["dayOffset"]?.jsonPrimitive?.intOrNull
    val name get() = document["name"]?.jsonPrimitive?.contentOrNull
    val exercises get() = document["exercises"]?.jsonArray?.map { ExercisePrescription(it.jsonObject) } ?: emptyList()
    fun toJson() = document
    companion object { fun fromJson(value: JsonElement) = PlanSession(value.jsonObject) }
}
class ExercisePrescription internal constructor(internal val document: JsonObject) {
    val prescriptionId get() = document["prescriptionId"]?.jsonPrimitive?.contentOrNull
    val exerciseId get() = document["exerciseId"]?.jsonPrimitive?.contentOrNull
    val exerciseName get() = document["exerciseName"]?.jsonPrimitive?.contentOrNull
    val order get() = document["order"]?.jsonPrimitive?.intOrNull
    val sets get() = document["sets"].toTargetRange()
    val reps get() = document["reps"].toTargetRange()
    val plannedSets get() = document["plannedSets"]?.jsonArray?.map { val x = it.jsonObject; SetPrescription(x["setPrescriptionId"]?.jsonPrimitive?.contentOrNull, x["setType"]?.jsonPrimitive?.content ?: "working", x["reps"].toTargetRange(), x["load"], x["effort"], x["volumeEligible"]?.jsonPrimitive?.booleanOrNull) } ?: emptyList()
    fun toJson() = document
}

@Serializable data class PlanActivation(val planId: String, val revisionId: String, val effectiveFrom: String, val effectiveTo: String? = null)
@Serializable data class TrainingHistory(val subjectId: String, val plans: List<WorkoutPlan> = emptyList(), val workouts: List<Workout> = emptyList(), val targets: List<VolumeTarget> = emptyList(), val planActivations: List<PlanActivation> = emptyList(), val metadata: Map<String, JsonElement> = emptyMap()) {
    fun plan(planId: String, revisionId: String? = null) = plans.firstOrNull { it.planId == planId && (revisionId == null || it.revisionId == revisionId) }
}
@Serializable sealed class TrainingHistoryWindow {
    @Serializable data object Last7Days : TrainingHistoryWindow()
    @Serializable data object Last28Days : TrainingHistoryWindow()
    @Serializable data object CurrentPlanCycle : TrainingHistoryWindow()
    @Serializable data object CurrentPhase : TrainingHistoryWindow()
    @Serializable data class Custom(val start: String, val end: String) : TrainingHistoryWindow()
}
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class ExerciseState(val exerciseId: String, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val lastPerformedAt: String? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val lastPrescription: JsonElement? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val lastActual: JsonElement? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val latestPerformance: JsonElement? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentPerformances: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentSessionCount: Int = 0, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentCompletedSetCount: Int = 0, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentReps: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentLoads: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) @SerialName("recentRPE") val recentRpe: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) @SerialName("recentRIR") val recentRir: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val recentSetTypes: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val prescriptionAdherence: JsonElement? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) @SerialName("prescriptionAdherenceByPrescriptionId") val adherenceByPrescriptionId: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val substitutionCount: Int = 0, @Transient val substitutionHistory: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val unplannedCount: Int = 0)
@Serializable data class MuscleState(val actualEffectiveSets: Double? = null, val target: Double? = null, val minimum: Double? = null, val maximum: Double? = null, val state: String? = null)
@Serializable data class FamilyState(val plannedSets: Double? = null, val target: Double? = null, val minimum: Double? = null, val maximum: Double? = null, val state: String? = null)
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class AdherenceState(val unplannedSets: Int? = null, val substitutionAdjustedCompletion: Double? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val sessionAdherence: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val exercisePrescriptionAdherence: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val missedScheduledOccurrences: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val repeatedSkippedExercises: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val repeatedSubstitutions: List<JsonElement> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val substitutionCountsByPrescription: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val substitutionHistoryByPrescription: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val unplannedExercises: List<JsonElement> = emptyList(), val skippedPrescriptionCounts: Map<String, Int> = emptyMap())
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class TrainingState(@EncodeDefault(EncodeDefault.Mode.ALWAYS) val stateVersion: String = "0.1.0", val subjectId: String, val asOf: String, val historyWindow: JsonElement? = null, val activePlan: JsonElement? = null, val revisionId: String? = null, val phase: JsonElement? = null, val cyclePosition: Int? = null, val exerciseState: Map<String, ExerciseState> = emptyMap(), val muscleState: Map<String, JsonElement> = emptyMap(), val familyState: Map<String, JsonElement> = emptyMap(), val adherenceState: AdherenceState? = null, val sessionState: List<JsonElement> = emptyList(), val provenance: Map<String, JsonElement> = emptyMap()) {
    companion object { fun fromJson(value: JsonElement) = apiJson.decodeFromJsonElement(serializer(), value) }
}

@Serializable data class PlanEvaluationSummary(val hardConstraintViolations: Int = 0, val targetGaps: Int = 0, val softPreferenceWarnings: Int = 0, val satisfiesHardConstraints: Boolean = true, val meetsTargetMinimums: Boolean = true, val evaluationStatus: String = "valid")
@Serializable(with = PlanEvaluationSerializer::class)
class PlanEvaluation internal constructor(internal val document: JsonObject) {
    val status get() = document["summary"]?.jsonObject?.get("evaluationStatus")?.jsonPrimitive?.content ?: "invalid"
    val summary get() = document["summary"]?.jsonObject?.let { PlanEvaluationSummary(it["hardConstraintViolations"]?.jsonPrimitive?.intOrNull ?: 0, it["targetGaps"]?.jsonPrimitive?.intOrNull ?: 0, it["softPreferenceWarnings"]?.jsonPrimitive?.intOrNull ?: 0, it["satisfiesHardConstraints"]?.jsonPrimitive?.booleanOrNull ?: false, it["meetsTargetMinimums"]?.jsonPrimitive?.booleanOrNull ?: false, it["evaluationStatus"]?.jsonPrimitive?.content ?: "invalid") } ?: PlanEvaluationSummary(evaluationStatus = "invalid")
    val warnings get() = document["warnings"]?.jsonArray?.mapNotNull { it.jsonPrimitive.contentOrNull } ?: emptyList()
    val provenance get() = document["provenance"]?.jsonObject ?: emptyMap()
    fun toJson() = document
    override fun equals(other: Any?) = other is PlanEvaluation && document == other.document
    override fun hashCode() = document.hashCode()
    companion object { fun fromJson(value: JsonElement) = PlanEvaluation(value.jsonObject) }
}
@Serializable data class PlanEvaluationRow(val actualEffectiveSets: Double? = null, val plannedSets: Double? = null, val minimum: Double? = null, val target: Double? = null, val maximum: Double? = null, val state: String? = null)
@Serializable data class PlanIssue(val code: String, val detail: String? = null, val exerciseId: String? = null, val familyId: String? = null, val sessionId: String? = null, val prescriptionId: String? = null)
@Serializable data class PlanChange(val type: String, val prescriptionId: String? = null, val exerciseId: String? = null, val before: Map<String, JsonElement> = emptyMap(), val after: Map<String, JsonElement> = emptyMap(), val reasonCodes: List<String> = emptyList(), val decisionIds: List<String> = emptyList())
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class CoachDecision(@EncodeDefault(EncodeDefault.Mode.ALWAYS) val schemaVersion: String = "0.1.0", val decisionId: String? = null, val decisionType: String, val policyId: String, val policyVersion: String, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val planId: String? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val revisionId: String? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val prescriptionId: String? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val exerciseId: String? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val before: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val after: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val reasonCodes: List<String> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val evidence: Map<String, JsonElement> = emptyMap(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val provenance: Map<String, JsonElement> = emptyMap())
@Serializable data class PlanGenerationRequest(val profile: TrainingProfile, val target: VolumeTarget, val policy: String = "full-body-general-v1", val trainingState: TrainingState? = null, val currentPlan: WorkoutPlan? = null, val requiredExerciseIds: List<String> = emptyList(), val lockedExerciseIds: List<String> = emptyList(), val requiredFamilyIds: List<String> = emptyList(), val additionalExclusions: List<String> = emptyList(), val options: JsonObject = JsonObject(emptyMap()))
@Serializable data class GeneratedPlanResult(val status: String, val plan: WorkoutPlan? = null, val evaluation: PlanEvaluation? = null, val policy: JsonElement? = null, val unsatisfiedConstraints: List<PlanIssue> = emptyList(), val unsatisfiedTargets: List<PlanIssue> = emptyList(), val unsatisfiedSoftPreferences: List<PlanIssue> = emptyList(), val provenance: Map<String, JsonElement> = emptyMap())
object InstantSerializer : KSerializer<Instant> {
    override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("Instant", PrimitiveKind.STRING)
    override fun serialize(encoder: Encoder, value: Instant) = encoder.encodeString(value.toString())
    override fun deserialize(decoder: Decoder): Instant = Instant.parse(decoder.decodeString())
}
@Serializable data class PlanAdaptationRequest(val profile: TrainingProfile, val target: VolumeTarget, val currentPlan: WorkoutPlan, val history: TrainingHistory? = null, val trainingState: TrainingState? = null, @Serializable(with = InstantSerializer::class) val asOf: Instant? = null, val policy: String = "general-adaptive-v1", val planningPolicy: String? = null)
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class AdaptivePlanResult(val status: String, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val currentPlan: WorkoutPlan? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val proposedPlan: WorkoutPlan? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val decisions: List<CoachDecision> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val currentEvaluation: PlanEvaluation? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val proposedEvaluation: PlanEvaluation? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val trainingState: TrainingState? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val changes: List<PlanChange> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val unresolvedIssues: List<PlanIssue> = emptyList(), @EncodeDefault(EncodeDefault.Mode.ALWAYS) val policy: JsonElement? = null, @EncodeDefault(EncodeDefault.Mode.ALWAYS) val provenance: Map<String, JsonElement> = emptyMap())
@Serializable data class IntentValidationIssue(val code: String, val field: String? = null, val message: String? = null)
@Serializable data class IntentValidationResult(val status: String, val issues: List<IntentValidationIssue> = emptyList()) { val isValid get() = status == "valid" && issues.isEmpty() }
@Serializable data class IntentPlanResult(val resolution: IntentResolutionResult, val generation: GeneratedPlanResult? = null)

abstract class JsonDocumentSerializer<T>(private val name: String, private val build: (JsonObject) -> T, private val read: (T) -> JsonObject) : KSerializer<T> {
    override val descriptor: SerialDescriptor = JsonElement.serializer().descriptor
    override fun serialize(encoder: Encoder, value: T) { (encoder as? JsonEncoder)?.encodeJsonElement(read(value)) ?: error("$name requires JSON") }
    override fun deserialize(decoder: Decoder): T = build((decoder as? JsonDecoder)?.decodeJsonElement()?.jsonObject ?: error("$name requires JSON"))
}
object WorkoutPlanSerializer : JsonDocumentSerializer<WorkoutPlan>("WorkoutPlan", ::WorkoutPlan, { it.document })
object PlanEvaluationSerializer : JsonDocumentSerializer<PlanEvaluation>("PlanEvaluation", ::PlanEvaluation, { it.document })
private fun JsonElement?.toTargetRange(): TargetRange? = when (this) { is JsonPrimitive -> jsonNumber?.let { TargetRange(target = it) }; is JsonObject -> TargetRange(this["min"].jsonNumber ?: this["minimumSets"].jsonNumber, this["target"].jsonNumber ?: this["targetSets"].jsonNumber, this["max"].jsonNumber ?: this["maximumSets"].jsonNumber); else -> null }
private val JsonElement?.jsonNumber get() = (this as? JsonPrimitive)?.doubleOrNull
