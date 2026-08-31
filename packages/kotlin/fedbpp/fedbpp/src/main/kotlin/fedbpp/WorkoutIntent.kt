package com.fedbpp

import kotlinx.serialization.Serializable
import kotlinx.serialization.EncodeDefault
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.JsonEncoder
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.put
import java.time.Instant
import java.time.ZoneOffset
import java.time.temporal.ChronoUnit

private object IntentPolicyCatalog {
    val root: JsonObject by lazy {
        val stream = IntentPolicyCatalog::class.java.classLoader.getResourceAsStream("intent-policies.json")
            ?: error("intent-policies.json is not packaged")
        stream.use { Json.parseToJsonElement(it.bufferedReader().readText()).jsonObject }
    }
    val goals get() = root["goalPolicies"]!!.jsonObject
    val environments get() = root["environmentPolicies"]!!.jsonObject
}

@Serializable data class IntRangeValue(val min: Int? = null, val target: Int? = null, val max: Int? = null)
@Serializable data class WorkoutSchedule(val cycleLengthDays: Int? = null, val sessionsPerCycle: IntRangeValue? = null, val preferredDayOffsets: List<Int> = emptyList(), val excludedDayOffsets: List<Int> = emptyList(), val preferredWeekdays: List<String> = emptyList(), val excludedWeekdays: List<String> = emptyList())
@Serializable data class SessionConstraints(val exercisesPerSession: IntRangeValue? = null)
@Serializable data class ExerciseConstraints(val requiredExerciseIds: List<String> = emptyList(), val lockedExerciseIds: List<String> = emptyList(), val excludedExerciseIds: List<String> = emptyList(), val requiredFamilyIds: List<String> = emptyList(), val excludedFamilyIds: List<String> = emptyList())
@Serializable data class WorkoutPreferences(val preferredExerciseIds: List<String> = emptyList(), val avoidedExerciseIds: List<String> = emptyList(), val preferredFamilyIds: List<String> = emptyList(), val avoidedFamilyIds: List<String> = emptyList())
@Serializable data class EquipmentOverrides(val addEquipment: List<String> = emptyList(), val removeEquipment: List<String> = emptyList())
@Serializable data class WorkoutIntent(val schemaVersion: String = "0.2.0", val intentId: String? = null, val subjectId: String? = null, val goal: String? = null, val requestedGoalPolicy: String? = null, val requestedPlanningPolicy: String? = null, val environment: String? = null, val schedule: WorkoutSchedule? = null, val sessionConstraints: SessionConstraints? = null, val exerciseConstraints: ExerciseConstraints? = null, val preferences: WorkoutPreferences? = null, val equipmentOverrides: EquipmentOverrides? = null, val continuity: String? = null, val useHistory: Boolean? = null, val historyWindow: String? = null)
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class ExplicitOverrides(
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val goalPolicy: Boolean = false,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val planningPolicy: Boolean = false,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val target: Boolean = false,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val trainingProfile: Boolean = false,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val equipmentAdded: List<String> = emptyList(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val equipmentRemoved: List<String> = emptyList()
)
@Serializable data class GoalPolicyReference(val policyId: String, val policyVersion: String, val description: String? = null)
@Serializable data class MissingInformation(val field: String, val reason: String)
@Serializable(with = IntentConflictSerializer::class) data class IntentConflict(val code: String, val detail: String? = null, val goal: String? = null, val requestedGoalPolicy: String? = null, val policyGoal: String? = null, val exerciseId: String? = null, val familyId: String? = null)

object IntentConflictSerializer : KSerializer<IntentConflict> {
    override val descriptor: SerialDescriptor = JsonElement.serializer().descriptor
    override fun serialize(encoder: Encoder, value: IntentConflict) {
        val out = buildJsonObject {
            put("code", value.code)
            value.detail?.let { put("detail", it) }; value.goal?.let { put("goal", it) }
            value.requestedGoalPolicy?.let { put("requestedGoalPolicy", it) }; value.policyGoal?.let { put("policyGoal", it) }
            value.exerciseId?.let { put("exerciseId", it) }; value.familyId?.let { put("familyId", it) }
        }
        (encoder as? JsonEncoder)?.encodeJsonElement(out) ?: error("IntentConflict requires JSON")
    }
    override fun deserialize(decoder: Decoder): IntentConflict {
        val value = (decoder as? JsonDecoder)?.decodeJsonElement()?.jsonObject ?: error("IntentConflict requires JSON")
        fun text(name: String) = value[name]?.takeUnless { it is JsonNull }?.jsonPrimitive?.contentOrNull
        return IntentConflict(value["code"]?.jsonPrimitive?.content ?: error("code is required"), text("detail"), text("goal"), text("requestedGoalPolicy"), text("policyGoal"), text("exerciseId"), text("familyId"))
    }
}
@OptIn(ExperimentalSerializationApi::class)
@Serializable data class IntentResolutionResult(
    val status: String,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val resolvedProfile: JsonElement? = null,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val resolvedTarget: JsonElement? = null,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val planningPolicy: String? = null,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val goalPolicy: GoalPolicyReference? = null,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val environmentPolicy: String? = null,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val generationOptions: JsonElement = JsonObject(emptyMap()),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val missingInformation: List<MissingInformation> = emptyList(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val warnings: List<String> = emptyList(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val conflicts: List<IntentConflict> = emptyList(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val defaultsApplied: List<String> = emptyList(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val explicitOverrides: ExplicitOverrides = ExplicitOverrides(),
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val provenance: Map<String, JsonElement> = emptyMap()
)

object WorkoutIntentValidator {
    val weekdays = listOf("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    fun validate(intent: WorkoutIntent, database: Database? = null, relationships: ExerciseRelationships? = null): List<String> {
        val errors = mutableSetOf<String>(); if (intent.schemaVersion != "0.1.0" && intent.schemaVersion != "0.2.0") errors += "schemaVersion: must be 0.2.0"
        val s = intent.schedule; val days = (s?.preferredWeekdays.orEmpty() + s?.excludedWeekdays.orEmpty()).toSet()
        if (days.isNotEmpty() && s?.cycleLengthDays != 7) errors += "schedule weekday fields require cycleLengthDays of 7"
        if (s?.preferredWeekdays.orEmpty().toSet().intersect(s?.excludedWeekdays.orEmpty().toSet()).isNotEmpty()) errors += "schedule: preferredWeekdays and excludedWeekdays conflict"
        if (s?.preferredDayOffsets.orEmpty().toSet().intersect(s?.excludedDayOffsets.orEmpty().toSet()).isNotEmpty()) errors += "schedule: preferredDayOffsets and excludedDayOffsets conflict"
        s?.sessionsPerCycle?.let { errors += rangeErrors(it, "schedule.sessionsPerCycle") }; intent.sessionConstraints?.exercisesPerSession?.let { errors += rangeErrors(it, "sessionConstraints.exercisesPerSession") }
        s?.cycleLengthDays?.let { if (it < 1) errors += "schedule.cycleLengthDays: must be at least 1" }
        fun nonNegative(r: IntRangeValue, field: String) { if (listOf(r.min, r.target, r.max).filterNotNull().any { it < 0 }) errors += "$field: values must be non-negative" }
        s?.sessionsPerCycle?.let { nonNegative(it, "schedule.sessionsPerCycle") }; intent.sessionConstraints?.exercisesPerSession?.let { nonNegative(it, "sessionConstraints.exercisesPerSession") }
        if (s != null) { if (s.preferredWeekdays.size != s.preferredWeekdays.toSet().size) errors += "schedule.preferredWeekdays: duplicate values"; if (s.excludedWeekdays.size != s.excludedWeekdays.toSet().size) errors += "schedule.excludedWeekdays: duplicate values"; if (s.preferredDayOffsets.size != s.preferredDayOffsets.toSet().size) errors += "schedule.preferredDayOffsets: duplicate values"; if (s.excludedDayOffsets.size != s.excludedDayOffsets.toSet().size) errors += "schedule.excludedDayOffsets: duplicate values" }
        val c = intent.exerciseConstraints; if (c != null && (c.requiredExerciseIds + c.lockedExerciseIds).toSet().intersect(c.excludedExerciseIds.toSet()).isNotEmpty()) errors += "exerciseConstraints: requiredExerciseIds conflicts with excludedExerciseIds"
        val p = intent.preferences; if (p != null && c != null) { if (p.preferredExerciseIds.toSet().intersect(c.excludedExerciseIds.toSet()).isNotEmpty()) errors += "preferences: preferredExerciseIds conflicts with excludedExerciseIds"; if (p.avoidedExerciseIds.toSet().intersect(c.excludedExerciseIds.toSet()).isNotEmpty()) errors += "preferences: avoidedExerciseIds conflicts with excludedExerciseIds"; if (p.preferredFamilyIds.toSet().intersect(c.excludedFamilyIds.toSet()).isNotEmpty()) errors += "preferences: preferredFamilyIds conflicts with excludedFamilyIds"; if (p.avoidedFamilyIds.toSet().intersect(c.excludedFamilyIds.toSet()).isNotEmpty()) errors += "preferences: avoidedFamilyIds conflicts with excludedFamilyIds" }
        if ((c?.requiredFamilyIds.orEmpty() + c?.excludedFamilyIds.orEmpty() + p?.preferredFamilyIds.orEmpty() + p?.avoidedFamilyIds.orEmpty()).isNotEmpty() && relationships == null) errors += "exercise family constraints require exercise relationships"
        if (intent.requestedGoalPolicy != null && intent.requestedGoalPolicy !in IntentPolicyCatalog.goals.keys) errors += "requestedGoalPolicy: unknown goal policy"
        intent.requestedGoalPolicy?.let { policyId ->
            val policyGoal = IntentPolicyCatalog.goals[policyId]?.jsonObject?.get("goal")?.jsonPrimitive?.content
            if (policyGoal != null && intent.goal != policyGoal) errors += "GOAL_POLICY_MISMATCH"
        }
        if (intent.requestedPlanningPolicy != null && intent.requestedPlanningPolicy !in setOf("full-body-general-v1", "upper-lower-general-v1")) errors += "requestedPlanningPolicy: unknown planning policy"
        if (intent.goal != null && intent.goal !in (IntentPolicyCatalog.goals.values.mapNotNull { it.jsonObject["goal"]?.jsonPrimitive?.content }.toSet() + setOf("muscular_endurance", "general_fitness", "skill_practice", "power"))) errors += "goal: unsupported value"
        if (intent.environment != null && intent.environment !in setOf("commercial_gym", "home_gym", "minimal_equipment", "bodyweight_only", "custom")) errors += "environment: unsupported value"
        if (intent.continuity != null && intent.continuity !in setOf("preserve", "neutral", "vary")) errors += "continuity: unsupported value"
        database?.let { db ->
            val c = intent.exerciseConstraints
            val p = intent.preferences
            listOf(
                "requiredExerciseIds" to c?.requiredExerciseIds.orEmpty(),
                "lockedExerciseIds" to c?.lockedExerciseIds.orEmpty(),
                "excludedExerciseIds" to c?.excludedExerciseIds.orEmpty(),
                "preferredExerciseIds" to p?.preferredExerciseIds.orEmpty(),
                "avoidedExerciseIds" to p?.avoidedExerciseIds.orEmpty()
            ).forEach { (field, values) -> values.filterNot { it in db.exerciseIds }.forEach { errors += "$field: unknown exerciseId: $it" } }
            val equipment = intent.equipmentOverrides
            listOf("addEquipment" to equipment?.addEquipment.orEmpty(), "removeEquipment" to equipment?.removeEquipment.orEmpty()).forEach { (field, values) -> values.filterNot { it in db.equipmentVocabulary }.forEach { errors += "equipmentOverrides.$field: unknown DB++ equipment value: $it" } }
            relationships?.let { rel ->
                val families = rel.families.keys
                listOf("requiredFamilyIds" to c?.requiredFamilyIds.orEmpty(), "excludedFamilyIds" to c?.excludedFamilyIds.orEmpty(), "preferredFamilyIds" to p?.preferredFamilyIds.orEmpty(), "avoidedFamilyIds" to p?.avoidedFamilyIds.orEmpty()).forEach { (field, values) -> values.filterNot { it in families }.forEach { errors += "$field: unknown familyId: $it" } }
            }
        }
        return errors.sorted()
    }
    private fun rangeErrors(r: IntRangeValue, field: String): List<String> = buildList { if (r.min != null && r.max != null && r.min!! > r.max!!) add("$field: min must not exceed max"); if (r.min != null && r.target != null && r.target!! < r.min!!) add("$field: target must not be below min"); if (r.max != null && r.target != null && r.target!! > r.max!!) add("$field: target must not exceed max") }
}

object WorkoutIntentResolver {
    fun resolve(intent: WorkoutIntent, database: Database? = null, profile: JsonElement? = null, target: JsonElement? = null, relationships: ExerciseRelationships? = null, history: JsonElement? = null, asOf: String? = null): IntentResolutionResult {
        val equipment = intent.equipmentOverrides ?: EquipmentOverrides(); val emptyOverrides = ExplicitOverrides(); val overrides = ExplicitOverrides(goalPolicy = intent.requestedGoalPolicy != null, planningPolicy = intent.requestedPlanningPolicy != null, target = target != null, trainingProfile = profile != null, equipmentAdded = equipment.addEquipment.toSet().sorted(), equipmentRemoved = equipment.removeEquipment.toSet().sorted())
        val errors = WorkoutIntentValidator.validate(intent, database, relationships)
        if (errors.isNotEmpty()) {
            if (errors == listOf("GOAL_POLICY_MISMATCH")) {
                val policyGoal = intent.requestedGoalPolicy?.let { IntentPolicyCatalog.goals[it]?.jsonObject?.get("goal")?.jsonPrimitive?.content }
                return IntentResolutionResult("invalid", conflicts = listOf(IntentConflict("GOAL_POLICY_MISMATCH", goal = intent.goal, requestedGoalPolicy = intent.requestedGoalPolicy, policyGoal = policyGoal)), explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
            }
            return IntentResolutionResult("invalid", conflicts = errors.map { IntentConflict("INVALID_INTENT", it) }, explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        }
        val s = intent.schedule; val suppliedObject = profile as? JsonObject; val suppliedEquipment = (suppliedObject?.get("equipment") as? kotlinx.serialization.json.JsonArray)?.map { it.jsonPrimitive.content }.orEmpty(); val missing = buildList { if (intent.goal == null) add(MissingInformation("goal", "required_for_goal_policy_resolution")); if (s?.cycleLengthDays == null) add(MissingInformation("schedule.cycleLengthDays", "required_for_schedule_resolution")); if (s?.sessionsPerCycle == null) add(MissingInformation("schedule.sessionsPerCycle", "required_for_schedule_resolution")); if (intent.environment == null && suppliedEquipment.isEmpty()) add(MissingInformation("environmentOrEquipment", "required_for_equipment_resolution")) }
        if (missing.isNotEmpty()) return IntentResolutionResult("needs_clarification", missingInformation = missing, explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        if (intent.environment == "home_gym" && suppliedEquipment.isEmpty() && intent.equipmentOverrides?.addEquipment.orEmpty().isEmpty()) return IntentResolutionResult("needs_clarification", missingInformation = listOf(MissingInformation("equipmentOverrides.addEquipment", "home_gym_has_no_v1_preset")))
        if (intent.environment == "custom" && suppliedEquipment.isEmpty() && intent.equipmentOverrides?.addEquipment.orEmpty().isEmpty()) return IntentResolutionResult("needs_clarification", missingInformation = listOf(MissingInformation("equipmentOverrides.addEquipment", "required_for_custom_environment")))
        val goalId = intent.requestedGoalPolicy ?: IntentPolicyCatalog.goals.entries.firstOrNull { it.value.jsonObject["goal"]?.jsonPrimitive?.content == intent.goal }?.key
        if (goalId == null) return IntentResolutionResult("needs_clarification", missingInformation = listOf(MissingInformation("requestedGoalPolicy", "no_default_goal_policy_for_goal")), explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val goalPolicy = IntentPolicyCatalog.goals[goalId]?.jsonObject
            ?: return IntentResolutionResult("invalid", conflicts = listOf(IntentConflict("INVALID_INTENT", "requestedGoalPolicy: unknown goal policy")))
        val description = goalPolicy["description"]?.jsonPrimitive?.content
        val policyVersion = goalPolicy["policyVersion"]?.jsonPrimitive?.content ?: "1"
        val policyGoal = goalPolicy["goal"]?.jsonPrimitive?.content
        if (intent.goal != policyGoal) return IntentResolutionResult("invalid", conflicts = listOf(IntentConflict("GOAL_POLICY_MISMATCH", goal = intent.goal, requestedGoalPolicy = goalId, policyGoal = policyGoal)), provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val environmentPolicy = IntentPolicyCatalog.environments.values
            .map { it.jsonObject }
            .firstOrNull { it["environment"]?.jsonPrimitive?.content == intent.environment }
        val environment = environmentPolicy?.get("policyId")?.jsonPrimitive?.content
        val envEquipment = environmentPolicy?.get("equipment")?.jsonArray?.map { it.jsonPrimitive.content }.orEmpty()
        val environmentVersion = environmentPolicy?.get("policyVersion")?.jsonPrimitive?.content ?: "1"
        var resolvedEquipment = ((if (suppliedEquipment.isEmpty()) envEquipment else suppliedEquipment) + equipment.addEquipment).toSet().minus(equipment.removeEquipment).toList().sorted()
        if (database != null) resolvedEquipment = resolvedEquipment.filter { it in database.equipmentVocabulary || it == "body only" }.sorted()
        val resolvedEnvironment = if (suppliedEquipment.isEmpty()) environment else null
        val defaults = buildList { if (intent.requestedGoalPolicy == null) add("goalPolicy"); if (intent.requestedPlanningPolicy == null) add("planningPolicy"); if (resolvedEnvironment != null) add("environmentPolicy") }
        val resolvedProfile = buildJsonObject {
            val supplied = profile as? JsonObject
            supplied?.forEach { (key, value) -> put(key, value) }
            put("schemaVersion", supplied?.get("schemaVersion") ?: JsonPrimitive(intent.schemaVersion))
            put("profileId", supplied?.get("profileId") ?: JsonPrimitive("resolved-profile"))
            put("subjectId", intent.subjectId?.let(::JsonPrimitive) ?: supplied?.get("subjectId") ?: kotlinx.serialization.json.JsonNull)
            put("goals", kotlinx.serialization.json.buildJsonArray { add(buildJsonObject { put("type", JsonPrimitive(intent.goal!!)) }) })
            put("equipment", kotlinx.serialization.json.buildJsonArray { resolvedEquipment.forEach { add(JsonPrimitive(it)) } })
            val suppliedPreferences = supplied?.get("exercisePreferences") as? JsonObject
            put("exercisePreferences", buildJsonObject {
                suppliedPreferences?.forEach { (key, value) -> put(key, value) }
                val input = intent.preferences
                listOf(
                    "preferredExerciseIds" to input?.preferredExerciseIds.orEmpty(),
                    "avoidedExerciseIds" to input?.avoidedExerciseIds.orEmpty(),
                    "preferredFamilyIds" to input?.preferredFamilyIds.orEmpty(),
                    "avoidedFamilyIds" to input?.avoidedFamilyIds.orEmpty()
                ).forEach { (key, values) ->
                    if (values.isNotEmpty()) {
                        val existing = (suppliedPreferences?.get(key) as? kotlinx.serialization.json.JsonArray)
                            ?.map { it.jsonPrimitive.content }.orEmpty()
                        put(key, kotlinx.serialization.json.buildJsonArray {
                            (existing + values).toSet().sorted().forEach { add(JsonPrimitive(it)) }
                        })
                    }
                }
            })
            put("constraints", buildJsonObject { val suppliedConstraints = supplied?.get("constraints") as? JsonObject; put("excludedExerciseIds", kotlinx.serialization.json.buildJsonArray { ((suppliedConstraints?.get("excludedExerciseIds") as? kotlinx.serialization.json.JsonArray)?.map { it.jsonPrimitive.content }.orEmpty() + intent.exerciseConstraints?.excludedExerciseIds.orEmpty()).toSet().sorted().forEach { add(JsonPrimitive(it)) } }); put("excludedFamilyIds", kotlinx.serialization.json.buildJsonArray { ((suppliedConstraints?.get("excludedFamilyIds") as? kotlinx.serialization.json.JsonArray)?.map { it.jsonPrimitive.content }.orEmpty() + intent.exerciseConstraints?.excludedFamilyIds.orEmpty()).toSet().sorted().forEach { add(JsonPrimitive(it)) } }) })
            put("availability", buildJsonObject { put("cycleLengthDays", JsonPrimitive(intent.schedule!!.cycleLengthDays!!)); put("sessionsPerCycle", buildJsonObject { val r = intent.schedule.sessionsPerCycle!!; r.min?.let { put("min", JsonPrimitive(it)) }; r.target?.let { put("target", JsonPrimitive(it)) }; r.max?.let { put("max", JsonPrimitive(it)) } }); put("preferredDayOffsets", kotlinx.serialization.json.buildJsonArray { (intent.schedule.preferredDayOffsets + intent.schedule.preferredWeekdays.mapNotNull { WorkoutIntentValidator.weekdays.indexOf(it).takeIf { n -> n >= 0 } }).toSet().sorted().forEach { add(JsonPrimitive(it)) } }); put("excludedDayOffsets", kotlinx.serialization.json.buildJsonArray { (intent.schedule.excludedDayOffsets + intent.schedule.excludedWeekdays.mapNotNull { WorkoutIntentValidator.weekdays.indexOf(it).takeIf { n -> n >= 0 } }).toSet().sorted().forEach { add(JsonPrimitive(it)) } }); intent.sessionConstraints?.exercisesPerSession?.let { r -> put("exercisesPerSession", buildJsonObject { r.min?.let { put("min", JsonPrimitive(it)) }; r.target?.let { put("target", JsonPrimitive(it)) }; r.max?.let { put("max", JsonPrimitive(it)) } }) } })
        }
        val defaultTarget = buildJsonObject { put("schemaVersion", "0.1.0"); put("targetId", "$goalId-default"); put("periodDays", intent.schedule!!.cycleLengthDays!!); put("muscles", goalPolicy["muscles"]!!); put("notes", description) }
        val mergedTarget = mergeTarget(defaultTarget, target); val targetErrors = validateTarget(mergedTarget); if (targetErrors.isNotEmpty()) return IntentResolutionResult("invalid", resolvedTarget = mergedTarget, conflicts = targetErrors.map { IntentConflict("TARGET_OVERRIDE_CONFLICT", detail = it) })
        val suppliedConstraints = (profile as? JsonObject)?.get("constraints") as? JsonObject
        val excludedExercises = ((suppliedConstraints?.get("excludedExerciseIds") as? JsonArray)?.map { it.jsonPrimitive.content }.orEmpty() + intent.exerciseConstraints?.excludedExerciseIds.orEmpty()).toSet()
        val excludedFamilies = ((suppliedConstraints?.get("excludedFamilyIds") as? JsonArray)?.map { it.jsonPrimitive.content }.orEmpty() + intent.exerciseConstraints?.excludedFamilyIds.orEmpty()).toSet()
        val constraintConflicts = (intent.exerciseConstraints?.requiredExerciseIds.orEmpty() + intent.exerciseConstraints?.lockedExerciseIds.orEmpty()).toSet().intersect(excludedExercises).sorted().map { IntentConflict("REQUIRED_EXERCISE_EXCLUDED", exerciseId = it) } + intent.exerciseConstraints?.requiredFamilyIds.orEmpty().toSet().intersect(excludedFamilies).sorted().map { IntentConflict("REQUIRED_FAMILY_EXCLUDED", familyId = it) }
        if (constraintConflicts.isNotEmpty()) return IntentResolutionResult("invalid", resolvedProfile = resolvedProfile, resolvedTarget = mergedTarget, conflicts = constraintConflicts)
        val historyWarnings = buildList { if (intent.useHistory == true && history == null) add("useHistory was requested but no history was provided"); if (intent.useHistory == true && history != null && asOf == null) add("useHistory was requested but as_of is required to derive TrainingState") }
        val options = buildJsonObject { put("continuity", intent.continuity ?: "neutral"); put("effortDefaults", goalPolicy["effort"]!!); put("repDefaults", goalPolicy["reps"]!!); put("requiredFamilyIds", kotlinx.serialization.json.buildJsonArray { intent.exerciseConstraints?.requiredFamilyIds.orEmpty().toSet().sorted().forEach { add(JsonPrimitive(it)) } }); if (intent.useHistory == true && history != null && asOf != null) { val historyWindow = when (intent.historyWindow) { "last_7_days" -> TrainingHistoryWindow.Last7Days; "current_plan_cycle" -> TrainingHistoryWindow.CurrentPlanCycle; "current_phase" -> TrainingHistoryWindow.CurrentPhase; else -> TrainingHistoryWindow.Last28Days }; put("trainingState", deriveTrainingStateCanonical(history, Instant.parse(asOf), historyWindow, database, relationships, mergedTarget)) } }
        val dbMetadata = database?.metadata.orEmpty()
        return IntentResolutionResult(if (defaults.isEmpty()) "resolved" else "resolved_with_defaults", planningPolicy = intent.requestedPlanningPolicy ?: goalPolicy["planningPolicy"]!!.jsonPrimitive.content, goalPolicy = GoalPolicyReference(goalId, policyVersion, description), environmentPolicy = resolvedEnvironment, defaultsApplied = defaults, explicitOverrides = overrides, resolvedProfile = resolvedProfile, resolvedTarget = mergedTarget, warnings = historyWarnings, generationOptions = options, provenance = buildMap { put("intentSchemaVersion", JsonPrimitive(intent.schemaVersion)); put("goalPolicy", buildJsonObject { put("policyId", goalId); put("policyVersion", policyVersion) }); put("environmentPolicy", resolvedEnvironment?.let { buildJsonObject { put("policyId", it); put("policyVersion", environmentVersion) } } ?: kotlinx.serialization.json.JsonNull); put("dbSchemaVersion", dbMetadata["schemaVersion"] ?: kotlinx.serialization.json.JsonNull); put("dbConverterVersion", dbMetadata["converterVersion"] ?: kotlinx.serialization.json.JsonNull); put("relationshipSchemaVersion", relationships?.schemaVersion?.let(::JsonPrimitive) ?: kotlinx.serialization.json.JsonNull) })
    }
}

fun deriveTrainingState(history: JsonElement, asOf: String): JsonElement {
    val root = history.jsonObject
    val asOfInstant = runCatching { Instant.parse(asOf) }.getOrNull()
        ?: throw IllegalArgumentException("asOf must be an offset-aware ISO-8601 timestamp")
    // Keep the legacy convenience overload semantically aligned with the
    // public state engine. The older bounded projection below is retained only
    // for source compatibility and is unreachable.
    return deriveTrainingStateCanonical(history, asOfInstant, TrainingHistoryWindow.Last28Days, null, null, null)
    val asDate = asOfInstant.atOffset(ZoneOffset.UTC).toLocalDate(); val start = asDate.minusDays(27)
    val workouts = root["workouts"]?.jsonArray.orEmpty().map { it.jsonObject }.filter { raw ->
        val stamp = raw["startTime"]?.jsonPrimitive?.content ?: ""
        val instant = runCatching { Instant.parse(stamp) }.getOrNull()
        instant != null && instant.atOffset(ZoneOffset.UTC).toLocalDate() >= start && instant <= asOfInstant
    }
    val counts = mutableMapOf<String, Pair<Int, Int>>()
    workouts.flatMap { it["exercises"]?.jsonArray.orEmpty() }.forEach { raw -> val e = raw.jsonObject; val id = e["exerciseId"]?.jsonPrimitive?.content ?: return@forEach; val old = counts[id] ?: (0 to 0); counts[id] = (old.first + 1) to (old.second + e["sets"]?.jsonArray.orEmpty().count { it.jsonObject["completed"]?.jsonPrimitive?.booleanOrNull == true }) }
    val exercises = buildJsonObject { counts.toSortedMap().forEach { (id, value) -> put(id, buildJsonObject { put("exerciseId", id); put("recentSessionCount", value.first); put("recentCompletedSetCount", value.second) }) } }
    val activePair = root["planActivations"]?.jsonArray.orEmpty().map { it.jsonObject }.mapNotNull { activation ->
        val from = activation["effectiveFrom"]?.jsonPrimitive?.content ?: return@mapNotNull null
        val fromInstant = runCatching { Instant.parse(from) }.getOrNull() ?: return@mapNotNull null
        val toInstant = activation["effectiveTo"]?.jsonPrimitive?.content?.let { runCatching { Instant.parse(it) }.getOrNull() }
        if (fromInstant > asOfInstant || (toInstant != null && asOfInstant >= toInstant)) return@mapNotNull null
        val plan = root["plans"]?.jsonArray.orEmpty().map { it.jsonObject }.firstOrNull { it["planId"] == activation["planId"] && it["revisionId"] == activation["revisionId"] } ?: return@mapNotNull null
        Triple(plan, activation, fromInstant)
    }.maxByOrNull { it.third }
    val activePlan = activePair?.let { (plan, _, fromInstant) -> val elapsed = ChronoUnit.DAYS.between(fromInstant.atOffset(ZoneOffset.UTC).toLocalDate(), asDate).coerceAtLeast(0); buildJsonObject { put("planId", plan["planId"]!!); put("revisionId", plan["revisionId"]!!); put("phaseId", kotlinx.serialization.json.JsonNull); put("cyclePosition", elapsed % (plan["cycle"]?.jsonObject?.get("lengthDays")?.jsonPrimitive?.intOrNull ?: 7) + 1) } } ?: JsonObject(emptyMap())
    val window = buildJsonObject { put("type", "last_28_days"); put("start", start.toString()); put("end", asDate.toString()) }
    return buildJsonObject { put("stateVersion", "0.1.0"); put("subjectId", root["subjectId"] ?: kotlinx.serialization.json.JsonNull); put("asOf", asOf); put("historyWindow", window); put("activePlan", activePlan); put("exerciseState", exercises); put("familyState", buildJsonObject { }); put("muscleState", buildJsonObject { }); put("adherenceState", buildJsonObject { }); put("sessionState", kotlinx.serialization.json.buildJsonArray { }); put("provenance", buildJsonObject { put("stateVersion", "0.1.0"); put("asOf", asOf); put("historyWindow", window) }) }
}

fun validateWorkoutIntent(intent: WorkoutIntent, database: Database? = null, relationships: ExerciseRelationships? = null): List<String> = WorkoutIntentValidator.validate(intent, database, relationships)
fun resolveIntent(intent: WorkoutIntent, database: Database? = null, profile: JsonElement? = null, target: JsonElement? = null, relationships: ExerciseRelationships? = null, history: JsonElement? = null, asOf: String? = null): IntentResolutionResult = WorkoutIntentResolver.resolve(intent, database, profile, target, relationships, history, asOf)
fun generatePlanFromIntent(intent: WorkoutIntent, database: Database, profile: JsonElement? = null, target: JsonElement? = null, relationships: ExerciseRelationships? = null, history: JsonElement? = null, asOf: String? = null): JsonElement {
    val resolution = resolveIntent(intent, database, profile, target, relationships, history, asOf)
    if (resolution.status !in setOf("resolved", "resolved_with_defaults")) return buildJsonObject { put("resolution", fedbppJson.encodeToJsonElement(IntentResolutionResult.serializer(), resolution)); put("generation", kotlinx.serialization.json.JsonNull) }
    val generationOptions = resolution.generationOptions as? JsonObject ?: JsonObject(emptyMap())
    val options = JsonObject(generationOptions.toMutableMap().apply { remove("trainingState"); remove("requiredFamilyIds"); if (intent.goal != "endurance") { remove("repDefaults"); remove("effortDefaults") } })
    val generated = generatePlan(resolution.resolvedProfile!!, resolution.resolvedTarget!!, database, relationships,
        intent.exerciseConstraints?.requiredExerciseIds.orEmpty() + intent.exerciseConstraints?.lockedExerciseIds.orEmpty(), options)
    return buildJsonObject { put("resolution", fedbppJson.encodeToJsonElement(IntentResolutionResult.serializer(), resolution)); put("generation", generated) }
}
fun resolveIntent(intent: WorkoutIntent, profile: JsonElement?, target: JsonElement?): IntentResolutionResult = WorkoutIntentResolver.resolve(intent, profile = profile, target = target)
fun decodeWorkoutIntent(json: String): WorkoutIntent {
    val element = Json.parseToJsonElement(json)
    require(element is JsonObject && element.containsKey("schemaVersion")) { "schemaVersion is required" }
    return fedbppJson.decodeFromJsonElement(WorkoutIntent.serializer(), element)
}

fun mergeTarget(base: JsonElement, explicit: JsonElement?): JsonElement {
    if (explicit !is JsonObject) return base
    if (base !is JsonObject) return explicit
    fun merge(a: JsonElement?, b: JsonElement): JsonElement = if (a is JsonObject && b is JsonObject) JsonObject(a.toMutableMap().apply { b.forEach { (key, value) -> this[key] = merge(this[key], value) } }) else b
    return JsonObject(base.toMutableMap().apply { explicit.forEach { (key, value) -> this[key] = if (key == "frequency" && value is JsonObject) { val f = (this[key] as? JsonObject)?.toMutableMap() ?: mutableMapOf(); f["muscles"] = merge(f["muscles"], value["muscles"] ?: JsonObject(emptyMap())); JsonObject(f) } else if (key in setOf("muscles", "movementPatterns", "families")) merge(this[key], value) else value } })
}

fun validateTarget(target: JsonElement): List<String> {
    val root = target as? JsonObject ?: return listOf("<root>: must be an object")
    fun check(section: String, values: JsonObject?, keys: Triple<String, String, String>): List<String> = values?.flatMap { (name, value) -> val r = value as? JsonObject ?: return@flatMap emptyList(); val min = r[keys.first]?.toString()?.toDoubleOrNull(); val mid = r[keys.second]?.toString()?.toDoubleOrNull(); val max = r[keys.third]?.toString()?.toDoubleOrNull(); buildList { if (min != null && max != null && min > max) add("$section.$name: minimum must not exceed maximum"); if (min != null && mid != null && mid < min) add("$section.$name: target must not be below minimum"); if (max != null && mid != null && mid > max) add("$section.$name: target must not exceed maximum") } } ?: emptyList()
    val frequency = (root["frequency"] as? JsonObject)?.get("muscles") as? JsonObject
    return check("muscles", root["muscles"] as? JsonObject, Triple("min", "target", "max")) + check("frequency.muscles", frequency, Triple("min", "target", "max")) + check("movementPatterns", root["movementPatterns"] as? JsonObject, Triple("minimumSets", "targetSets", "maximumSets")) + check("families", root["families"] as? JsonObject, Triple("minimumSets", "targetSets", "maximumSets"))
}
