package com.fedbpp

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonPrimitive

@Serializable data class IntRangeValue(val min: Int? = null, val target: Int? = null, val max: Int? = null)
@Serializable data class WorkoutSchedule(val cycleLengthDays: Int? = null, val sessionsPerCycle: IntRangeValue? = null, val preferredDayOffsets: List<Int> = emptyList(), val excludedDayOffsets: List<Int> = emptyList(), val preferredWeekdays: List<String> = emptyList(), val excludedWeekdays: List<String> = emptyList())
@Serializable data class SessionConstraints(val exercisesPerSession: IntRangeValue? = null)
@Serializable data class ExerciseConstraints(val requiredExerciseIds: List<String> = emptyList(), val lockedExerciseIds: List<String> = emptyList(), val excludedExerciseIds: List<String> = emptyList(), val requiredFamilyIds: List<String> = emptyList(), val excludedFamilyIds: List<String> = emptyList())
@Serializable data class WorkoutPreferences(val preferredExerciseIds: List<String> = emptyList(), val avoidedExerciseIds: List<String> = emptyList(), val preferredFamilyIds: List<String> = emptyList(), val avoidedFamilyIds: List<String> = emptyList())
@Serializable data class EquipmentOverrides(val addEquipment: List<String> = emptyList(), val removeEquipment: List<String> = emptyList())
@Serializable data class WorkoutIntent(val schemaVersion: String = "0.1.0", val intentId: String? = null, val subjectId: String? = null, val goal: String? = null, val requestedGoalPolicy: String? = null, val requestedPlanningPolicy: String? = null, val environment: String? = null, val schedule: WorkoutSchedule? = null, val sessionConstraints: SessionConstraints? = null, val exerciseConstraints: ExerciseConstraints? = null, val preferences: WorkoutPreferences? = null, val equipmentOverrides: EquipmentOverrides? = null, val continuity: String? = null, val useHistory: Boolean? = null, val historyWindow: String? = null)
@Serializable data class ExplicitOverrides(val goalPolicy: Boolean = false, val planningPolicy: Boolean = false, val target: Boolean = false, val trainingProfile: Boolean = false, val equipmentAdded: List<String> = emptyList(), val equipmentRemoved: List<String> = emptyList())
@Serializable data class GoalPolicyReference(val policyId: String, val policyVersion: String = "1", val description: String? = null)
@Serializable data class MissingInformation(val field: String, val reason: String)
@Serializable data class IntentConflict(val code: String, val detail: String? = null, val goal: String? = null, val requestedGoalPolicy: String? = null, val policyGoal: String? = null, val exerciseId: String? = null, val familyId: String? = null)
@Serializable data class IntentResolutionResult(val status: String, val resolvedProfile: JsonElement? = null, val resolvedTarget: JsonElement? = null, val planningPolicy: String? = null, val goalPolicy: GoalPolicyReference? = null, val environmentPolicy: String? = null, val generationOptions: JsonElement = JsonObject(emptyMap()), val missingInformation: List<MissingInformation> = emptyList(), val warnings: List<String> = emptyList(), val conflicts: List<IntentConflict> = emptyList(), val defaultsApplied: List<String> = emptyList(), val explicitOverrides: ExplicitOverrides = ExplicitOverrides(), val provenance: Map<String, JsonElement> = emptyMap())

object WorkoutIntentValidator {
    val weekdays = listOf("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    fun validate(intent: WorkoutIntent): List<String> {
        val errors = mutableSetOf<String>(); if (intent.schemaVersion != "0.1.0") errors += "schemaVersion: must be 0.1.0"
        val s = intent.schedule; val days = (s?.preferredWeekdays.orEmpty() + s?.excludedWeekdays.orEmpty()).toSet()
        if (days.isNotEmpty() && s?.cycleLengthDays != 7) errors += "schedule weekday fields require cycleLengthDays of 7"
        if (s?.preferredWeekdays.orEmpty().toSet().intersect(s?.excludedWeekdays.orEmpty().toSet()).isNotEmpty()) errors += "schedule: preferredWeekdays and excludedWeekdays conflict"
        if (s?.preferredDayOffsets.orEmpty().toSet().intersect(s?.excludedDayOffsets.orEmpty().toSet()).isNotEmpty()) errors += "schedule: preferredDayOffsets and excludedDayOffsets conflict"
        s?.sessionsPerCycle?.let { errors += rangeErrors(it, "schedule.sessionsPerCycle") }; intent.sessionConstraints?.exercisesPerSession?.let { errors += rangeErrors(it, "sessionConstraints.exercisesPerSession") }
        val c = intent.exerciseConstraints; if (c != null && (c.requiredExerciseIds + c.lockedExerciseIds).toSet().intersect(c.excludedExerciseIds.toSet()).isNotEmpty()) errors += "exerciseConstraints: requiredExerciseIds conflicts with excludedExerciseIds"
        if ((intent.goal == "hypertrophy" && intent.requestedGoalPolicy == "general-strength-v1") || (intent.goal == "strength" && intent.requestedGoalPolicy == "general-hypertrophy-v1")) errors += "GOAL_POLICY_MISMATCH"
        if (intent.requestedGoalPolicy != null && intent.requestedGoalPolicy !in setOf("general-hypertrophy-v1", "general-strength-v1")) errors += "requestedGoalPolicy: unknown goal policy"
        if (intent.requestedPlanningPolicy != null && intent.requestedPlanningPolicy !in setOf("full-body-general-v1", "upper-lower-general-v1")) errors += "requestedPlanningPolicy: unknown planning policy"
        return errors.sorted()
    }
    private fun rangeErrors(r: IntRangeValue, field: String): List<String> = buildList { if (r.min != null && r.max != null && r.min!! > r.max!!) add("$field: min must not exceed max"); if (r.min != null && r.target != null && r.target!! < r.min!!) add("$field: target must not be below min"); if (r.max != null && r.target != null && r.target!! > r.max!!) add("$field: target must not exceed max") }
}

object WorkoutIntentResolver {
    fun resolve(intent: WorkoutIntent, profile: JsonElement? = null, target: JsonElement? = null): IntentResolutionResult {
        val equipment = intent.equipmentOverrides ?: EquipmentOverrides(); val emptyOverrides = ExplicitOverrides(); val overrides = ExplicitOverrides(goalPolicy = intent.requestedGoalPolicy != null, planningPolicy = intent.requestedPlanningPolicy != null, target = target != null, trainingProfile = profile != null, equipmentAdded = equipment.addEquipment.sorted(), equipmentRemoved = equipment.removeEquipment.sorted())
        val errors = WorkoutIntentValidator.validate(intent)
        if (errors.isNotEmpty()) return IntentResolutionResult("invalid", conflicts = errors.map { IntentConflict(if (it == "GOAL_POLICY_MISMATCH") it else "INVALID_INTENT", it) }, explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val s = intent.schedule; val missing = buildList { if (intent.goal == null) add(MissingInformation("goal", "required_for_goal_policy_resolution")); if (s?.cycleLengthDays == null) add(MissingInformation("schedule.cycleLengthDays", "required_for_schedule_resolution")); if (s?.sessionsPerCycle == null) add(MissingInformation("schedule.sessionsPerCycle", "required_for_schedule_resolution")); if (intent.environment == null && profile == null) add(MissingInformation("environmentOrEquipment", "required_for_equipment_resolution")) }
        if (missing.isNotEmpty()) return IntentResolutionResult("needs_clarification", missingInformation = missing, explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val goalId = intent.requestedGoalPolicy ?: when (intent.goal) { "hypertrophy" -> "general-hypertrophy-v1"; "strength" -> "general-strength-v1"; else -> null }
        if (goalId == null) return IntentResolutionResult("needs_clarification", missingInformation = listOf(MissingInformation("requestedGoalPolicy", "no_default_goal_policy_for_goal")), explicitOverrides = emptyOverrides, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val description = if (goalId == "general-strength-v1") "Minimal generic strength defaults; exercise-specific strength programming remains out of scope." else "General, conservative coverage defaults; not an optimal prescription."
        if (goalId == "general-strength-v1" && intent.goal != "strength" || goalId == "general-hypertrophy-v1" && intent.goal != "hypertrophy") return IntentResolutionResult("invalid", conflicts = listOf(IntentConflict("GOAL_POLICY_MISMATCH", goal = intent.goal, requestedGoalPolicy = goalId, policyGoal = if (goalId == "general-strength-v1") "strength" else "hypertrophy")), provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion)))
        val environment = mapOf("commercial_gym" to "commercial-gym-general-v1", "bodyweight_only" to "bodyweight-only-v1", "minimal_equipment" to "minimal-equipment-general-v1")[intent.environment]
        val envEquipment = mapOf("commercial_gym" to listOf("bands", "barbell", "body only", "cable", "dumbbell", "e-z curl bar", "exercise ball", "kettlebells", "machine", "medicine ball"), "bodyweight_only" to listOf("body only"), "minimal_equipment" to listOf("bands", "body only", "dumbbell"))[intent.environment].orEmpty()
        val suppliedObject = profile as? JsonObject
        val profileEquipment = (suppliedObject?.get("equipment") as? kotlinx.serialization.json.JsonArray)?.map { it.jsonPrimitive.content }
        val resolvedEquipment = ((profileEquipment ?: envEquipment) + equipment.addEquipment).toSet().minus(equipment.removeEquipment).toList().sorted()
        val defaults = buildList { if (intent.requestedGoalPolicy == null) add("goalPolicy"); if (intent.requestedPlanningPolicy == null) add("planningPolicy"); if (environment != null && profile == null) add("environmentPolicy") }
        val resolvedProfile = buildJsonObject {
            val supplied = profile as? JsonObject
            supplied?.forEach { (key, value) -> put(key, value) }
            if (!containsKey("schemaVersion")) put("schemaVersion", "0.1.0")
            if (!containsKey("profileId")) put("profileId", "resolved-profile")
            put("subjectId", intent.subjectId ?: supplied?.get("subjectId") ?: kotlinx.serialization.json.JsonNull)
            put("goals", kotlinx.serialization.json.buildJsonArray { add(buildJsonObject { put("type", intent.goal!!) }) })
            put("equipment", kotlinx.serialization.json.buildJsonArray { resolvedEquipment.forEach { add(it) } })
            put("exercisePreferences", supplied?.get("exercisePreferences") ?: JsonObject(emptyMap()))
            put("constraints", supplied?.get("constraints") ?: buildJsonObject { put("excludedExerciseIds", kotlinx.serialization.json.buildJsonArray { }); put("excludedFamilyIds", kotlinx.serialization.json.buildJsonArray { }) })
            put("availability", buildJsonObject { put("cycleLengthDays", intent.schedule!!.cycleLengthDays!!); put("sessionsPerCycle", buildJsonObject { val r = intent.schedule.sessionsPerCycle!!; r.min?.let { put("min", it) }; r.target?.let { put("target", it) }; r.max?.let { put("max", it) } }); put("preferredDayOffsets", kotlinx.serialization.json.buildJsonArray { (intent.schedule.preferredDayOffsets + intent.schedule.preferredWeekdays.mapNotNull { WorkoutIntentValidator.weekdays.indexOf(it).takeIf { n -> n >= 0 } }).toSet().sorted().forEach { add(it) } }); put("excludedDayOffsets", kotlinx.serialization.json.buildJsonArray { (intent.schedule.excludedDayOffsets + intent.schedule.excludedWeekdays.mapNotNull { WorkoutIntentValidator.weekdays.indexOf(it).takeIf { n -> n >= 0 } }).toSet().sorted().forEach { add(it) } }); intent.sessionConstraints?.exercisesPerSession?.let { r -> put("exercisesPerSession", buildJsonObject { r.min?.let { put("min", it) }; r.target?.let { put("target", it) }; r.max?.let { put("max", it) } }) } })
        }
        val defaultTarget = buildJsonObject { put("schemaVersion", "0.1.0"); put("targetId", "$goalId-default"); put("periodDays", intent.schedule!!.cycleLengthDays!!); put("muscles", buildJsonObject { if (goalId == "general-strength-v1") { put("chest", buildJsonObject { put("target", 3) }); put("quadriceps", buildJsonObject { put("target", 3) }); put("hamstrings", buildJsonObject { put("target", 2) }) } else { put("chest", buildJsonObject { put("target", 6) }); put("lats", buildJsonObject { put("target", 6) }); put("quadriceps", buildJsonObject { put("target", 6) }); put("hamstrings", buildJsonObject { put("target", 4) }) } }); put("notes", description) }
        return IntentResolutionResult(if (defaults.isEmpty()) "resolved" else "resolved_with_defaults", planningPolicy = intent.requestedPlanningPolicy ?: "full-body-general-v1", goalPolicy = GoalPolicyReference(goalId, description = description), environmentPolicy = environment, defaultsApplied = defaults, explicitOverrides = overrides, resolvedProfile = resolvedProfile, resolvedTarget = target ?: defaultTarget, generationOptions = buildJsonObject { put("continuity", intent.continuity ?: "neutral"); put("effortDefaults", buildJsonObject { put("rir", 2) }); put("repDefaults", buildJsonObject { if (goalId == "general-strength-v1") { put("min", 3); put("target", 5); put("max", 6) } else { put("min", 6); put("target", 8); put("max", 12) } }); put("requiredFamilyIds", kotlinx.serialization.json.buildJsonArray { }) }, provenance = mapOf("intentSchemaVersion" to JsonPrimitive(intent.schemaVersion), "goalPolicy" to buildJsonObject { put("policyId", goalId); put("policyVersion", "1") }, "environmentPolicy" to (environment?.let { buildJsonObject { put("policyId", it); put("policyVersion", "1") } } ?: kotlinx.serialization.json.JsonNull)))
    }
}

fun validateWorkoutIntent(intent: WorkoutIntent): List<String> = WorkoutIntentValidator.validate(intent)
fun resolveIntent(intent: WorkoutIntent, profile: JsonElement? = null, target: JsonElement? = null): IntentResolutionResult = WorkoutIntentResolver.resolve(intent, profile, target)

fun mergeTarget(base: JsonElement, explicit: JsonElement?): JsonElement {
    if (explicit !is JsonObject) return base
    if (base !is JsonObject) return explicit
    fun merge(a: JsonElement?, b: JsonElement): JsonElement = if (a is JsonObject && b is JsonObject) JsonObject(a.toMutableMap().apply { b.forEach { (key, value) -> this[key] = merge(this[key], value) } }) else b
    return JsonObject(base.toMutableMap().apply { explicit.forEach { (key, value) -> this[key] = if (key == "frequency" && value is JsonObject) { val f = (this[key] as? JsonObject)?.toMutableMap() ?: mutableMapOf(); f["muscles"] = merge(f["muscles"], value["muscles"] ?: JsonObject(emptyMap())); JsonObject(f) } else if (key in setOf("muscles", "movementPatterns", "families")) merge(this[key], value) else value } })
}

fun validateTarget(target: JsonElement): List<String> {
    val root = target as? JsonObject ?: return listOf("<root>: must be an object")
    fun check(section: String, values: JsonObject?, keys: Triple<String, String, String>): List<String> = values?.flatMap { (name, value) -> val r = value as? JsonObject ?: return@flatMap emptyList(); val min = r[keys.first]?.toString()?.toDoubleOrNull(); val mid = r[keys.second]?.toString()?.toDoubleOrNull(); val max = r[keys.third]?.toString()?.toDoubleOrNull(); buildList { if (min != null && max != null && min > max) add("$section.$name: min must not exceed max"); if (min != null && mid != null && mid < min) add("$section.$name: target must not be below min"); if (max != null && mid != null && mid > max) add("$section.$name: target must not exceed max") } } ?: emptyList()
    val frequency = (root["frequency"] as? JsonObject)?.get("muscles") as? JsonObject
    return check("muscles", root["muscles"] as? JsonObject, Triple("min", "target", "max")) + check("frequency.muscles", frequency, Triple("min", "target", "max")) + check("movementPatterns", root["movementPatterns"] as? JsonObject, Triple("minimumSets", "targetSets", "maximumSets")) + check("families", root["families"] as? JsonObject, Triple("minimumSets", "targetSets", "maximumSets"))
}
