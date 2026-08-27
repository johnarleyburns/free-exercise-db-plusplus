package com.fedbpp

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import kotlin.math.round

/**
 * Native implementation of the canonical PLAN evaluator.  Its JSON result is
 * deliberately shaped like Python's ``fedbpp.evaluate_plan`` result so the
 * generator and public engine façade share one evaluator gate.
 */
private const val EVALUATION_VERSION = "0.1.0"
private const val EVALUATION_POLICY = "plan-evaluation-v1"

private fun JsonElement?.obj(): JsonObject = this as? JsonObject ?: JsonObject(emptyMap())
private fun JsonElement?.arr(): JsonArray = this as? JsonArray ?: JsonArray(emptyList())
private fun JsonElement?.string(): String? = (this as? JsonPrimitive)?.content
private fun JsonElement?.number(): Double? = (this as? JsonPrimitive)?.doubleOrNull
private fun clean(value: Double): Double = round(value * 1_000_000.0) / 1_000_000.0
private fun jo(vararg values: Pair<String, JsonElement>): JsonObject = JsonObject(linkedMapOf(*values))
private fun jn(value: Double?): JsonElement = value?.let(::JsonPrimitive) ?: JsonNull

private data class Range(val min: Double? = null, val target: Double? = null, val max: Double? = null)
private fun range(value: JsonElement?): Range {
    if (value !is JsonObject) return Range(target = value.number())
    return Range(value["min"]?.number() ?: value["minimumSets"]?.number(), value["target"]?.number() ?: value["targetSets"]?.number(), value["max"]?.number() ?: value["maximumSets"]?.number())
}
private fun state(actual: Double, range: Range): String = when {
    range.min != null && actual < range.min -> "below_minimum"
    range.max != null && actual > range.max -> "above_maximum"
    range.target == null -> "within_range"
    actual == range.target -> "at_target"
    actual < range.target -> "within_range_below_target"
    else -> "within_range_above_target"
}
private fun plannedSets(rx: JsonObject): Double {
    val explicit = rx["plannedSets"]?.arr()
    if (explicit != null && explicit.isNotEmpty()) return explicit.size.toDouble()
    val v = rx["sets"]
    return when (v) { is JsonPrimitive -> v.doubleOrNull ?: 0.0; is JsonObject -> range(v).target ?: range(v).min ?: range(v).max ?: 0.0; else -> 0.0 }
}

private data class Coverage(
    val direct: MutableMap<String, Double> = sortedMapOf(), val indirect: MutableMap<String, Double> = sortedMapOf(),
    val stabilizer: MutableMap<String, Double> = sortedMapOf(), val patterns: MutableMap<String, Double> = sortedMapOf(),
    val muscleSessions: MutableMap<String, MutableSet<String>> = sortedMapOf(), val patternSessions: MutableMap<String, MutableSet<String>> = sortedMapOf(),
    var planned: Double = 0.0, var mapped: Double = 0.0, var unmapped: Double = 0.0, var ineligible: Double = 0.0,
    val unmappedRx: MutableList<String> = mutableListOf(), val ineligibleRx: MutableList<String> = mutableListOf()
)

private fun add(table: MutableMap<String, Double>, key: String, value: Double) { table[key] = clean((table[key] ?: 0.0) + value) }
private fun mapNumbers(input: Map<String, Double>): JsonObject = buildJsonObject { input.toSortedMap().forEach { (k, v) -> put(k, JsonPrimitive(clean(v))) } }
private fun setCredits(database: Database): Triple<Double, Double, Double> {
    val credits = database.metadata["setCredits"].obj()
    return Triple(credits["direct"].number() ?: 1.0, credits["indirect"].number() ?: 0.5, credits["stabilizer"].number() ?: 0.0)
}

private fun coverage(plan: JsonObject, database: Database): Coverage {
    val result = Coverage()
    for (sessionValue in plan["sessions"].arr()) {
        val session = sessionValue.obj(); val sid = session["planSessionId"].string() ?: ""
        for (rxValue in session["exercises"].arr()) {
            val rx = rxValue.obj(); val sets = plannedSets(rx); result.planned += sets
            val id = rx["exerciseId"].string(); val exercise = id?.let { database.exercises[it] }
            if (exercise == null) { result.unmapped += sets; rx["prescriptionId"].string()?.let(result.unmappedRx::add); continue }
            result.mapped += sets
            if (!exercise.annotation.volumeEligible) { result.ineligible += sets; rx["prescriptionId"].string()?.let(result.ineligibleRx::add); continue }
            exercise.annotation.direct.forEach { add(result.direct, it, sets); result.muscleSessions.getOrPut(it) { sortedSetOf() }.add(sid) }
            exercise.annotation.indirect.forEach { add(result.indirect, it, sets); result.muscleSessions.getOrPut(it) { sortedSetOf() }.add(sid) }
            exercise.annotation.stabilizers.forEach { add(result.stabilizer, it, sets) }
            exercise.annotation.patterns.forEach { add(result.patterns, it, sets); result.patternSessions.getOrPut(it) { sortedSetOf() }.add(sid) }
        }
    }
    return result
}

private fun finding(type: String, vararg values: Pair<String, JsonElement>): JsonObject = buildJsonObject { put("type", JsonPrimitive(type)); values.sortedBy { it.first }.forEach { put(it.first, it.second) } }

/** Evaluate a PLAN without a Python bridge or source-tree dependency. */
fun evaluatePlan(planValue: JsonElement, database: Database, profileValue: JsonElement? = null, targetValue: JsonElement? = null, relationships: ExerciseRelationships? = null): JsonElement {
    val plan = planValue.obj(); val profile = profileValue as? JsonObject; val target = targetValue as? JsonObject
    val c = coverage(plan, database); val days = plan["cycle"].obj()["lengthDays"]?.jsonPrimitive?.intOrNull ?: 7
    val credits = setCredits(database); val muscles = (c.direct.keys + c.indirect.keys + c.stabilizer.keys).toSortedSet()
    val effective = muscles.associateWith { clean((c.direct[it] ?: 0.0) * credits.first + (c.indirect[it] ?: 0.0) * credits.second + (c.stabilizer[it] ?: 0.0) * credits.third) }
    val targetDays = target?.get("periodDays")?.number() ?: days.toDouble(); val targetScale = targetDays / days
    val muscleRows = buildJsonObject {
        val configured = target?.get("muscles").obj()
        (configured.keys + effective.keys).toSortedSet().forEach { muscle ->
            val r = range(configured[muscle]); val actual = clean((effective[muscle] ?: 0.0) * targetScale)
            val row = jo(
                "actualEffectiveSets" to JsonPrimitive(actual), "minimum" to jn(r.min), "target" to jn(r.target),
                "maximum" to jn(r.max), "min" to jn(r.min), "max" to jn(r.max),
                "differenceFromTarget" to jn(r.target?.let { clean(actual - it) }),
                "planEffectiveSetRange" to jo("min" to JsonPrimitive(actual), "target" to JsonPrimitive(actual), "max" to JsonPrimitive(actual)),
                "state" to JsonPrimitive(if (configured[muscle] == null) "not_targeted" else state(actual, r)),
                "periodDays" to JsonPrimitive(targetDays)
            )
            put(muscle, row)
        }
    }
    val frequencyRows = buildJsonObject {
        target?.get("frequency").obj()["muscles"].obj().toSortedMap().forEach { (muscle, spec) ->
            val exposures = c.muscleSessions[muscle]?.size ?: 0; val normalized = clean(exposures * 7.0 / days); val r = range(spec)
            put(muscle, jo("plannedExposuresPerNativeCycle" to JsonPrimitive(exposures), "normalizedExposuresPer7Days" to JsonPrimitive(normalized), "minimum" to jn(r.min), "target" to jn(r.target), "maximum" to jn(r.max), "state" to JsonPrimitive(state(normalized, r))))
        }
    }
    val patternRows = buildJsonObject {
        target?.get("movementPatterns").obj().toSortedMap().forEach { (pattern, spec) ->
            val actual = c.patterns[pattern] ?: 0.0; val r = range(spec)
            put(pattern, jo("plannedSets" to JsonPrimitive(actual), "minimum" to jn(r.min), "target" to jn(r.target), "maximum" to jn(r.max), "state" to JsonPrimitive(state(actual, r))))
        }
    }
    val familyCounts = sortedMapOf<String, Double>(); val familyCoverage = buildJsonObject {
        if (relationships != null) database.exercises.keys.sorted().forEach { id -> relationships.familyFor(id)?.familyId?.let { family -> familyCounts.putIfAbsent(family, 0.0) } }
        for (sessionValue in plan["sessions"].arr()) for (rxValue in sessionValue.obj()["exercises"].arr()) {
            val id = rxValue.obj()["exerciseId"].string() ?: continue; relationships?.familyFor(id)?.familyId?.let { add(familyCounts, it, plannedSets(rxValue.obj())) }
        }
        familyCounts.forEach { (id, sets) -> put(id, jo("familyId" to JsonPrimitive(id), "plannedSets" to JsonPrimitive(sets))) }
    }
    val familyTargets = buildJsonObject {
        target?.get("families").obj().toSortedMap().forEach { (family, spec) ->
            val actual = familyCounts[family] ?: 0.0; val r = range(spec)
            put(family, jo("plannedSets" to JsonPrimitive(actual), "minimum" to jn(r.min), "target" to jn(r.target), "maximum" to jn(r.max), "state" to JsonPrimitive(state(actual, r))))
        }
    }
    val hard = mutableListOf<JsonObject>(); val soft = mutableListOf<JsonObject>(); val supported = sortedSetOf<String>(); val unsupported = mutableListOf<JsonObject>(); val unknown = mutableListOf<JsonObject>()
    val availability = profile?.get("availability").obj(); val excludedDays = availability["excludedDayOffsets"].arr().mapNotNull { it.jsonPrimitive.intOrNull }.toSet()
    val preferences = profile?.get("exercisePreferences").obj(); val constraints = profile?.get("constraints").obj()
    val excludedExercise = constraints["excludedExerciseIds"].arr().mapNotNull { it.string() }.toSet(); val excludedFamilies = constraints["excludedFamilyIds"].arr().mapNotNull { it.string() }.toSet()
    val preferredExercise = preferences["preferredExerciseIds"].arr().mapNotNull { it.string() }.toSet(); val avoidedExercise = preferences["avoidedExerciseIds"].arr().mapNotNull { it.string() }.toSet(); val preferredFamilies = preferences["preferredFamilyIds"].arr().mapNotNull { it.string() }.toSet(); val avoidedFamilies = preferences["avoidedFamilyIds"].arr().mapNotNull { it.string() }.toSet()
    val availableEquipment = profile?.get("equipment").arr().mapNotNull { it.string() }.toSet(); val body = setOf("body only", "bodyweight", "no equipment", "none")
    for (sessionValue in plan["sessions"].arr()) {
        val session = sessionValue.obj(); val sid = session["planSessionId"].string() ?: ""
        if (session["dayOffset"]?.jsonPrimitive?.intOrNull in excludedDays) hard += finding("excluded_day_offset", "sessionId" to JsonPrimitive(sid), "dayOffset" to (session["dayOffset"] ?: JsonNull))
        for (rxValue in session["exercises"].arr()) {
            val rx = rxValue.obj(); val id = rx["exerciseId"].string() ?: continue; val pid = rx["prescriptionId"].string() ?: ""
            val family = relationships?.familyFor(id)?.familyId
            if (id in excludedExercise) hard += finding("excluded_exercise", "exerciseId" to JsonPrimitive(id), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            if (family in excludedFamilies) hard += finding("excluded_family", "exerciseId" to JsonPrimitive(id), "familyId" to JsonPrimitive(family!!), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            if (id in preferredExercise) soft += finding("preferred_exercise_used", "exerciseId" to JsonPrimitive(id), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            if (id in avoidedExercise) soft += finding("avoided_exercise_used", "exerciseId" to JsonPrimitive(id), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            if (family in preferredFamilies) soft += finding("preferred_family_used", "exerciseId" to JsonPrimitive(id), "familyId" to JsonPrimitive(family!!), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            if (family in avoidedFamilies) soft += finding("avoided_family_used", "exerciseId" to JsonPrimitive(id), "familyId" to JsonPrimitive(family!!), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
            val exercise = database.exercises[id]
            if (exercise == null) { unknown += finding("unknown_exercise", "exerciseId" to JsonPrimitive(id), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid)); continue }
            val equipment = exercise.source["equipment"].string()
            when { equipment == null || equipment in setOf("None", "other") -> unknown += finding("unknown_equipment", "exerciseId" to JsonPrimitive(id), "equipment" to (exercise.source["equipment"] ?: JsonNull), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid))
                equipment in body && availableEquipment.intersect(body).isNotEmpty() -> supported += id
                equipment in availableEquipment -> supported += id
                else -> { val f = finding("unsupported_equipment", "equipment" to JsonPrimitive(equipment), "exerciseId" to JsonPrimitive(id), "prescriptionId" to JsonPrimitive(pid), "sessionId" to JsonPrimitive(sid)); unsupported += f; hard += f }
            }
        }
    }
    val exerciseCounts = buildJsonObject {
        val r = range(availability["exercisesPerSession"]); if (profile != null && listOf(r.min, r.target, r.max).any { it != null }) for (sessionValue in plan["sessions"].arr()) {
            val session = sessionValue.obj(); val n = session["exercises"].arr().size.toDouble(); val s = state(n, r); val sid = session["planSessionId"].string() ?: ""
            put(sid, jo("exerciseCount" to JsonPrimitive(n.toInt()), "minimum" to jn(r.min), "target" to jn(r.target), "maximum" to jn(r.max), "state" to JsonPrimitive(s)))
            if (s == "below_minimum" || s == "above_maximum") hard += finding("exercise_count", "sessionId" to JsonPrimitive(sid), "exerciseCount" to JsonPrimitive(n.toInt()), "minimum" to jn(r.min), "maximum" to jn(r.max))
            else if (r.target != null && n != r.target) soft += finding("exercise_count_target_miss", "sessionId" to JsonPrimitive(sid), "exerciseCount" to JsonPrimitive(n.toInt()), "target" to jn(r.target))
        }
    }
    val sessionRange = range(availability["sessionsPerCycle"]); val sessionCount = plan["sessions"].arr().size.toDouble(); val availabilityResult = if (profile == null || availability.isEmpty()) jo("plannedSessions" to JsonPrimitive(sessionCount.toInt()), "state" to JsonPrimitive("not_evaluated")) else jo("plannedSessions" to JsonPrimitive(sessionCount.toInt()), "min" to jn(sessionRange.min), "target" to jn(sessionRange.target), "max" to jn(sessionRange.max), "state" to JsonPrimitive(state(sessionCount, sessionRange)))
    val targetGaps = listOf(muscleRows, frequencyRows, patternRows, familyTargets).sumOf { rows -> rows.values.count { it.obj()["state"].string() == "below_minimum" } }
    val mappedFraction = if (c.planned == 0.0) 1.0 else clean(c.mapped / c.planned)
    val completeness = jo("plannedSets" to JsonPrimitive(clean(c.planned)), "plannedSetRange" to jo("min" to JsonPrimitive(clean(c.planned)), "target" to JsonPrimitive(clean(c.planned)), "max" to JsonPrimitive(clean(c.planned))), "mappedSets" to JsonPrimitive(clean(c.mapped)), "mappedSetRange" to jo("min" to JsonPrimitive(clean(c.mapped)), "target" to JsonPrimitive(clean(c.mapped)), "max" to JsonPrimitive(clean(c.mapped))), "unmappedSets" to JsonPrimitive(clean(c.unmapped)), "unmappedSetRange" to jo("min" to JsonPrimitive(clean(c.unmapped)), "target" to JsonPrimitive(clean(c.unmapped)), "max" to JsonPrimitive(clean(c.unmapped))), "ineligibleSets" to JsonPrimitive(clean(c.ineligible)), "ineligibleSetRange" to jo("min" to JsonPrimitive(clean(c.ineligible)), "target" to JsonPrimitive(clean(c.ineligible)), "max" to JsonPrimitive(clean(c.ineligible))), "mappedFraction" to JsonPrimitive(mappedFraction), "unmappedPrescriptions" to JsonArray(c.unmappedRx.sorted().map(::JsonPrimitive)), "ineligiblePrescriptions" to JsonArray(c.ineligibleRx.sorted().map(::JsonPrimitive)))
    val warnings = mutableSetOf<String>(); if (c.unmapped != 0.0 || c.ineligible != 0.0 || unknown.isNotEmpty()) warnings += "coverage is incomplete for one or more PLAN exercises"; if (profile?.get("availability").obj()["minutesPerSession"] != null) warnings += "duration estimation is not evaluated by duration-estimation-v1 because PLAN rest/transition inputs are not complete"; if (target?.get("families").obj()?.isNotEmpty() == true && relationships == null) warnings += "family targets cannot be evaluated because relationship artifact was not provided"
    val sortedHard = hard.sortedBy { "${it["type"].string()}:${it["exerciseId"].string() ?: it["familyId"].string() ?: it["sessionId"].string() ?: ""}:${it["sessionId"].string() ?: ""}:${it["prescriptionId"].string() ?: ""}" }
    val status = if (hard.isNotEmpty()) "hard_constraint_violation" else if (mappedFraction < 1 || (target?.get("families").obj()?.isNotEmpty() == true && relationships == null)) "incomplete_coverage" else if (targetGaps > 0) "valid_with_target_gaps" else "valid"
    return buildJsonObject {
        put("summary", jo("hardConstraintViolations" to JsonPrimitive(sortedHard.size), "targetGaps" to JsonPrimitive(targetGaps), "softPreferenceWarnings" to JsonPrimitive(soft.size), "satisfiesHardConstraints" to JsonPrimitive(sortedHard.isEmpty()), "meetsTargetMinimums" to JsonPrimitive(targetGaps == 0), "evaluationStatus" to JsonPrimitive(status)))
        put("muscleCoverage", muscleRows); put("frequency", frequencyRows); put("movementPatterns", patternRows); put("families", jo("coverage" to if (relationships == null) jo("available" to JsonPrimitive(false), "reason" to JsonPrimitive("relationship artifact not provided")) else familyCoverage, "targets" to familyTargets)); put("equipment", jo("supportedExercises" to JsonArray(supported.map(::JsonPrimitive)), "unsupportedExercises" to JsonArray(unsupported.sortedBy { it["exerciseId"].string() ?: "" }), "unknownEquipmentExercises" to JsonArray(unknown.sortedBy { it["exerciseId"].string() ?: "" }))); put("availability", availabilityResult); put("exerciseCounts", exerciseCounts)
        put("preferences", jo("preferredExercisesUsed" to JsonArray(soft.filter { it["type"].string() == "preferred_exercise_used" }.mapNotNull { it["exerciseId"] }.distinct().sortedBy { it.string() }), "preferredFamiliesUsed" to JsonArray(soft.filter { it["type"].string() == "preferred_family_used" }.mapNotNull { it["familyId"] }.distinct().sortedBy { it.string() }), "avoidedExercisesUsed" to JsonArray(soft.filter { it["type"].string() == "avoided_exercise_used" }.mapNotNull { it["exerciseId"] }.distinct().sortedBy { it.string() }), "avoidedFamiliesUsed" to JsonArray(soft.filter { it["type"].string() == "avoided_family_used" }.mapNotNull { it["familyId"] }.distinct().sortedBy { it.string() }), "findings" to JsonArray(soft.sortedBy { "${it["type"].string()}:${it["exerciseId"].string() ?: it["familyId"].string() ?: ""}" })))
        put("constraints", jo("violations" to JsonArray(sortedHard))); put("coverageCompleteness", completeness); put("warnings", JsonArray(warnings.sorted().map(::JsonPrimitive)))
        put("provenance", jo("analysisVersion" to JsonPrimitive(EVALUATION_VERSION), "analysisPolicy" to JsonPrimitive(EVALUATION_POLICY), "planSchemaVersion" to (plan["schemaVersion"] ?: JsonNull), "profileSchemaVersion" to (profile?.get("schemaVersion") ?: JsonNull), "targetSchemaVersion" to (target?.get("schemaVersion") ?: JsonNull), "relationshipSchemaVersion" to (relationships?.schemaVersion?.let(::JsonPrimitive) ?: JsonNull), "dbSchemaVersion" to (database.metadata["schemaVersion"] ?: JsonNull), "dbConverterVersion" to (database.metadata["converterVersion"] ?: JsonNull), "dbUpstreamSha256" to (database.metadata["upstream"].obj()["sha256"] ?: JsonNull), "setCredits" to jo("direct" to JsonPrimitive(credits.first), "indirect" to JsonPrimitive(credits.second), "stabilizer" to JsonPrimitive(credits.third)), "durationPolicy" to if (profile?.get("availability").obj()["minutesPerSession"] != null) JsonPrimitive("duration-estimation-v1") else JsonNull))
    }
}
