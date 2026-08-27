package com.fedbpp

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put

/**
 * Native deterministic allocation entry point.  It is deliberately evaluator
 * gated: every accepted allocation is checked through [evaluatePlan].
 */
fun generatePlan(profile: JsonElement, target: JsonElement, database: Database, relationships: ExerciseRelationships? = null, requiredExerciseIds: List<String> = emptyList(), options: JsonObject = JsonObject(emptyMap())): JsonElement {
    val p = profile as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val t = target as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    if ((t["families"] as? JsonObject)?.isNotEmpty() == true && relationships == null) return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val availability = p["availability"] as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val sessionRange = availability["sessionsPerCycle"] as? JsonObject ?: JsonObject(emptyMap())
    val counts = canonicalSessionCounts(sessionRange["min"]?.jsonPrimitive?.intOrNull, sessionRange["target"]?.jsonPrimitive?.intOrNull, sessionRange["max"]?.jsonPrimitive?.intOrNull, 3)
    if (counts.conflicts.isNotEmpty()) return generationResult("unsatisfiable", null, null, counts.conflicts)
    val cycle = availability["cycleLengthDays"]?.jsonPrimitive?.intOrNull ?: t["periodDays"]?.jsonPrimitive?.intOrNull ?: 7
    val preferred = availability["preferredDayOffsets"]?.jsonArray.orEmpty().mapNotNull { it.jsonPrimitive.intOrNull }
    val excluded = availability["excludedDayOffsets"]?.jsonArray.orEmpty().mapNotNull { it.jsonPrimitive.intOrNull }.toSet()
    val count = counts.counts.first(); val offsets = canonicalDayOffsets(cycle, count, preferred, excluded) ?: return generationResult("unsatisfiable", null, null, listOf("SESSION_COUNT_CONFLICT"))
    val candidates = canonicalCandidatePool(database, p, relationships)
    if (candidates.isEmpty()) return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
    val maxExercises = ((availability["exercisesPerSession"] as? JsonObject)?.get("max")?.jsonPrimitive?.intOrNull)
    val sessions = offsets.mapIndexed { i, day -> mutableListOf<JsonObject>() to day }
    fun canAdd(index: Int, candidate: PlanningCandidate): Boolean = sessions[index].first.any { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId } || maxExercises == null || sessions[index].first.size < maxExercises
    fun add(index: Int, candidate: PlanningCandidate) {
        val existing = sessions[index].first.firstOrNull { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId }
        if (existing != null) { val changed = existing.toMutableMap(); changed["sets"] = JsonPrimitive((changed["sets"]?.jsonPrimitive?.intOrNull ?: 0) + 1); sessions[index].first[sessions[index].first.indexOf(existing)] = JsonObject(changed); return }
        val n = sessions[index].first.size + 1
        sessions[index].first += buildJsonObject { put("prescriptionId", "rx-${index + 1}-${n}"); put("exerciseId", candidate.exerciseId); put("order", n); put("sets", 1); put("reps", buildJsonObject { put("min", 6); put("target", 8); put("max", 10) }); put("effort", buildJsonObject { put("rir", 2) }); put("setType", "working") }
    }
    val required = requiredExerciseIds.toSet(); for (id in required.sorted()) {
        val candidate = candidates.firstOrNull { it.exerciseId == id } ?: return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
        val slot = sessions.indices.firstOrNull { canAdd(it, candidate) } ?: return generationResult("unsatisfiable", null, null, listOf("EXERCISE_COUNT_CONFLICT")); add(slot, candidate)
    }
    fun plan(): JsonObject = buildJsonObject { put("schemaVersion", "0.2.0"); put("planId", options["planId"] ?: JsonPrimitive("generated-plan")); put("revisionId", options["revisionId"] ?: JsonPrimitive("r1")); put("name", options["name"] ?: JsonPrimitive("Generated full-body-general-v1")); put("description", JsonNull); put("cycle", buildJsonObject { put("lengthDays", cycle) }); put("sessions", buildJsonArray { sessions.forEachIndexed { i, pair -> add(buildJsonObject { put("planSessionId", "session-${i + 1}"); put("dayOffset", pair.second); put("name", "Session ${i + 1}"); put("exercises", JsonArray(pair.first)) }) } }) }
    var current = plan(); var evaluation = evaluatePlan(current, database, p, t, relationships).jsonObject
    // Canonical first phase: satisfy muscle minima, greatest deficit then rank.
    while (true) {
        val deficit = evaluation["muscleCoverage"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["actualEffectiveSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Triple(min - actual, muscle, value) else null }.sortedWith(compareByDescending<Triple<Double, String, JsonObject>> { it.first }.thenBy { it.second }).firstOrNull() ?: break
        val ranked = rankCandidates(candidates.filter { targetContribution(it, "muscle", deficit.second, database) > 0 }, required, emptySet(), contribution = { targetContribution(it, "muscle", deficit.second, database) })
        var accepted = false
        for (candidate in ranked) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Target phase follows minimum fulfillment; target shortfalls remain soft gaps.
    while (true) {
        val deficit = evaluation["muscleCoverage"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val targetValue = value["target"]?.jsonPrimitive?.doubleOrNull; val actual = value["actualEffectiveSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (targetValue != null && actual < targetValue) Pair(muscle, targetValue - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rankCandidates(candidates.filter { targetContribution(it, "muscle", deficit.first, database) > 0 }, required, emptySet(), contribution = { targetContribution(it, "muscle", deficit.first, database) })
        var accepted = false
        for (candidate in ranked) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // A canonical PLAN must populate every constructed session to the explicit
    // per-session minimum without breaching evaluator maxima.
    val minimumExercises = ((availability["exercisesPerSession"] as? JsonObject)?.get("min")?.jsonPrimitive?.intOrNull ?: 1).coerceAtLeast(1)
    for (slot in sessions.indices) while (sessions[slot].first.size < minimumExercises) {
        val ranked = rankCandidates(candidates.filter { candidate ->
            canAdd(slot, candidate) && sessions[slot].first.none { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId }
        }, required, emptySet(), contribution = { 0.0 })
        val candidate = ranked.firstOrNull() ?: return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
        val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
        val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
        if (above) { sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }; return generationResult("unsatisfiable", null, null, listOf("SESSION_COUNT_CONFLICT")) }
        current = proposed; evaluation = proposedEvaluation
    }
    // Family target minima when relationships exist.
    while (true) {
        val deficit = evaluation["families"]?.jsonObject?.get("targets")?.jsonObject.orEmpty().mapNotNull { (family, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["plannedSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(family, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rankCandidates(candidates.filter { targetContribution(it, "family", deficit.first, database) > 0 }, required, emptySet(), contribution = { targetContribution(it, "family", deficit.first, database) })
        var accepted = false
        for (candidate in ranked) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Movement-pattern minima.
    while (true) {
        val deficit = evaluation["movementPatterns"]?.jsonObject.orEmpty().mapNotNull { (pattern, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["plannedSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(pattern, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rankCandidates(candidates.filter { targetContribution(it, "pattern", deficit.first, database) > 0 }, required, emptySet(), contribution = { targetContribution(it, "pattern", deficit.first, database) })
        var accepted = false
        for (candidate in ranked) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Distribute frequency minima across distinct sessions.
    while (true) {
        val deficit = evaluation["frequency"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["normalizedExposuresPer7Days"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(muscle, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rankCandidates(candidates.filter { targetContribution(it, "frequency", deficit.first, database) > 0 }, required, emptySet(), contribution = { targetContribution(it, "frequency", deficit.first, database) })
        var accepted = false
        for (candidate in ranked) for (slot in sessions.indices.sortedWith(compareBy<Int> { sessionIndex ->
            val hasExposure = sessions[sessionIndex].first.any { rx -> database.exercises[rx["exerciseId"]?.jsonPrimitive?.content]?.annotation?.let { deficit.first in it.direct || deficit.first in it.indirect } == true }
            if (hasExposure) 1 else 0
        }.thenBy { sessions[it].first.size }.thenBy { it })) {
            val hasExposure = sessions[slot].first.any { rx -> database.exercises[rx["exerciseId"]?.jsonPrimitive?.content]?.annotation?.let { deficit.first in it.direct || deficit.first in it.indirect } == true }
            if (hasExposure || !canAdd(slot, candidate)) continue
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    if (evaluation["summary"]!!.jsonObject["satisfiesHardConstraints"]!!.jsonPrimitive.content == "false") return generationResult("unsatisfiable", null, evaluation, listOf("EVALUATOR_HARD_CONSTRAINT"))
    val status = if (evaluation["summary"]!!.jsonObject["meetsTargetMinimums"]!!.jsonPrimitive.content == "true") "generated" else "generated_with_target_gaps"
    return generationResult(status, current, evaluation, emptyList())
}

private fun generationResult(status: String, plan: JsonObject?, evaluation: JsonObject?, constraints: List<String>): JsonElement = buildJsonObject {
    val targetRows = mutableListOf<JsonObject>()
    fun collect(rows: JsonObject?, actualKey: String, code: String) = rows.orEmpty().forEach { (id, raw) ->
        val row = raw.jsonObject; val actual = row[actualKey]?.jsonPrimitive?.doubleOrNull ?: 0.0
        row["minimum"]?.jsonPrimitive?.doubleOrNull?.takeIf { actual < it }?.let { minimum -> targetRows += buildJsonObject { put("code", "${code}_UNSATISFIED"); put("targetId", id); put("deficit", minimum - actual) } }
        row["maximum"]?.jsonPrimitive?.doubleOrNull?.takeIf { actual > it }?.let { maximum -> targetRows += buildJsonObject { put("code", "${code}_MAXIMUM_EXCEEDED"); put("targetId", id); put("excess", actual - maximum) } }
    }
    evaluation?.let { value -> collect(value["muscleCoverage"] as? JsonObject, "actualEffectiveSets", "MUSCLE_TARGET"); collect(value["frequency"] as? JsonObject, "normalizedExposuresPer7Days", "FREQUENCY_TARGET"); collect(value["movementPatterns"] as? JsonObject, "plannedSets", "PATTERN_TARGET"); collect(value["families"]?.jsonObject?.get("targets") as? JsonObject, "plannedSets", "FAMILY_TARGET") }
    put("status", status); put("plan", plan ?: JsonNull); put("evaluation", evaluation ?: JsonNull); put("policy", buildJsonObject { put("policyId", "full-body-general-v1"); put("policyVersion", "1") }); put("selectionRationale", JsonArray(emptyList())); put("unsatisfiedConstraints", buildJsonArray { constraints.forEach { add(buildJsonObject { put("code", it) }) } }); put("unsatisfiedTargets", JsonArray(targetRows.sortedWith(compareBy<JsonObject> { it["code"]?.jsonPrimitive?.content ?: "" }.thenBy { it["targetId"]?.jsonPrimitive?.content ?: "" }))); put("unsatisfiedSoftPreferences", JsonArray(emptyList())); put("provenance", buildJsonObject { put("generatorVersion", "0.1.0"); put("policyId", "full-body-general-v1") })
}
