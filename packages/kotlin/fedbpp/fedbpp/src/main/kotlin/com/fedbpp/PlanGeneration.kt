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
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.put

private fun JsonElement?.planInt(): Int? = this?.jsonPrimitive?.intOrNull ?: this?.jsonPrimitive?.doubleOrNull?.toInt()

/**
 * Native deterministic allocation entry point.  It is deliberately evaluator
 * gated: every accepted allocation is checked through [evaluatePlan].
 */
fun generatePlan(profile: JsonElement, target: JsonElement, database: Database, relationships: ExerciseRelationships? = null, requiredExerciseIds: List<String> = emptyList(), options: JsonObject = JsonObject(emptyMap())): JsonElement {
    val p = profile as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val t = target as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val targetErrors = validateTarget(t)
    if (targetErrors.isNotEmpty()) return generationInvalid(database, p, t, targetErrors.map { "INVALID_INPUT" to it })
    if ((t["families"] as? JsonObject)?.isNotEmpty() == true && relationships == null) return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val locked = options["lockedExerciseIds"]?.jsonArray.orEmpty().map { it.jsonPrimitive.content }.toSet()
    if (locked.isNotEmpty() && options["currentPlan"] == null) return generationConflict(database, p, t, relationships, locked.map { it to "locked exercises require current_plan" })
    val availability = p["availability"] as? JsonObject ?: return generationResult("invalid_input", null, null, listOf("INVALID_INPUT"))
    val sessionRange = availability["sessionsPerCycle"] as? JsonObject ?: JsonObject(emptyMap())
    val counts = canonicalSessionCounts(sessionRange["min"].planInt(), sessionRange["target"].planInt(), sessionRange["max"].planInt(), 3)
    if (counts.conflicts.isNotEmpty()) return generationResult("unsatisfiable", null, null, counts.conflicts)
    val cycle = availability["cycleLengthDays"]?.jsonPrimitive?.intOrNull ?: t["periodDays"]?.jsonPrimitive?.intOrNull ?: 7
    val dayPreferred = availability["preferredDayOffsets"]?.jsonArray.orEmpty().mapNotNull { it.jsonPrimitive.intOrNull }
    val excluded = availability["excludedDayOffsets"]?.jsonArray.orEmpty().mapNotNull { it.jsonPrimitive.intOrNull }.toSet()
    val count = counts.counts.first(); val offsets = canonicalDayOffsets(cycle, count, dayPreferred, excluded) ?: return generationResult("unsatisfiable", null, null, listOf("SESSION_COUNT_CONFLICT"))
    val additionalExclusions = options["additionalExclusions"]?.jsonArray.orEmpty().map { it.jsonPrimitive.content }.toSet()
    val candidates = canonicalCandidatePool(database, p, relationships, additionalExclusions)
    if (candidates.isEmpty()) return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
    val maxExercises = ((availability["exercisesPerSession"] as? JsonObject)?.get("max").planInt())
    val sessions = offsets.mapIndexed { i, day -> mutableListOf<JsonObject>() to day }
    fun canAdd(index: Int, candidate: PlanningCandidate): Boolean = sessions[index].first.any { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId } || maxExercises == null || sessions[index].first.size < maxExercises
    fun add(index: Int, candidate: PlanningCandidate) {
        val existing = sessions[index].first.firstOrNull { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId }
        if (existing != null) { val changed = existing.toMutableMap(); changed["sets"] = JsonPrimitive((changed["sets"]?.jsonPrimitive?.intOrNull ?: 0) + 1); sessions[index].first[sessions[index].first.indexOf(existing)] = JsonObject(changed); return }
        val n = sessions[index].first.size + 1
        sessions[index].first += buildJsonObject { put("prescriptionId", "rx-${(index + 1).toString().padStart(2, '0')}-${n.toString().padStart(2, '0')}"); put("exerciseId", candidate.exerciseId); put("exerciseName", database.getExercise(candidate.exerciseId).source["name"]?.jsonPrimitive?.content ?: candidate.exerciseId); put("order", n); put("sets", 1); put("reps", buildJsonObject { put("min", 6); put("target", 8); put("max", 10) }); put("effort", buildJsonObject { put("rir", 2) }); put("setType", "working") }
    }
    val required = requiredExerciseIds.toSet(); for (id in required.sorted()) {
        val candidate = candidates.firstOrNull { it.exerciseId == id } ?: return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
        val slot = sessions.indices.firstOrNull { canAdd(it, candidate) } ?: return generationResult("unsatisfiable", null, null, listOf("EXERCISE_COUNT_CONFLICT")); add(slot, candidate)
    }
    fun plan(): JsonObject = buildJsonObject { put("schemaVersion", "0.2.0"); put("planId", options["planId"] ?: JsonPrimitive("generated-plan")); put("revisionId", options["revisionId"] ?: JsonPrimitive("r1")); put("name", options["name"] ?: JsonPrimitive("Generated full-body-general-v1")); put("description", JsonNull); put("cycle", buildJsonObject { put("lengthDays", cycle) }); put("sessions", buildJsonArray { sessions.forEachIndexed { i, pair -> add(buildJsonObject { put("planSessionId", "session-${i + 1}"); put("dayOffset", pair.second); put("name", "Session ${i + 1}"); put("exercises", JsonArray(pair.first)) }) } }) }
    var current = plan(); var evaluation = evaluatePlan(current, database, p, t, relationships).jsonObject
    val existing = options["currentPlan"]?.planJsonObjectOrEmpty?.get("sessions").planJsonArrayOrEmpty()
        .flatMap { it.planJsonObjectOrEmpty["exercises"].planJsonArrayOrEmpty() }
        .mapNotNull { it.planJsonObjectOrEmpty["exerciseId"]?.jsonPrimitive?.contentOrNull }.toSet()
    val state = options["trainingState"]?.planJsonObjectOrEmpty
    val history: Map<String, JsonObject> = state?.get("exerciseState")?.planJsonObjectOrEmpty
        ?.mapValues { (_, value) -> value as? JsonObject ?: JsonObject(emptyMap()) } ?: emptyMap()
    val preferences = p["exercisePreferences"].planJsonObjectOrEmpty
    val preferred = preferences["preferredExerciseIds"].planJsonArrayOrEmpty().mapNotNull { it.jsonPrimitive.contentOrNull }.toSet()
    val avoided = preferences["avoidedExerciseIds"].planJsonArrayOrEmpty().mapNotNull { it.jsonPrimitive.contentOrNull }.toSet()
    val preferredFamilies = preferences["preferredFamilyIds"].planJsonArrayOrEmpty().mapNotNull { it.jsonPrimitive.contentOrNull }.toSet()
    val avoidedFamilies = preferences["avoidedFamilyIds"].planJsonArrayOrEmpty().mapNotNull { it.jsonPrimitive.contentOrNull }.toSet()
    val continuity = options["continuity"]?.jsonPrimitive?.content ?: "preserve"
    fun rank(values: List<PlanningCandidate>, contribution: (PlanningCandidate) -> Double) =
        rankCandidates(values, required, existing, history, continuity, preferred, preferredFamilies, avoided, avoidedFamilies, contribution)
    // Canonical first phase: satisfy muscle minima, greatest deficit then rank.
    while (true) {
        val deficit = evaluation["muscleCoverage"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["actualEffectiveSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Triple(min - actual, muscle, value) else null }.sortedWith(compareByDescending<Triple<Double, String, JsonObject>> { it.first }.thenBy { it.second }).firstOrNull() ?: break
        val ranked = rank(candidates.filter { targetContribution(it, "muscle", deficit.second, database) > 0 }) { targetContribution(it, "muscle", deficit.second, database) }
        var accepted = false
        for (candidate in ranked) if (!accepted) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Target phase follows minimum fulfillment; target shortfalls remain soft gaps.
    while (true) {
        val deficit = evaluation["muscleCoverage"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val targetValue = value["target"]?.jsonPrimitive?.doubleOrNull; val actual = value["actualEffectiveSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (targetValue != null && actual < targetValue) Pair(muscle, targetValue - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rank(candidates.filter { targetContribution(it, "muscle", deficit.first, database) > 0 }) { targetContribution(it, "muscle", deficit.first, database) }
        var accepted = false
        for (candidate in ranked) if (!accepted) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // A canonical PLAN must populate every constructed session to the explicit
    // per-session minimum without breaching evaluator maxima.
    val minimumExercises = ((availability["exercisesPerSession"] as? JsonObject)?.get("min").planInt() ?: 1).coerceAtLeast(1)
    for (slot in sessions.indices) while (sessions[slot].first.size < minimumExercises) {
        val ranked = rank(candidates.filter { candidate ->
            canAdd(slot, candidate) && sessions[slot].first.none { it["exerciseId"]?.jsonPrimitive?.content == candidate.exerciseId }
        }) { 0.0 }
        val candidate = ranked.firstOrNull() ?: return generationResult("unsatisfiable", null, null, listOf("NO_ELIGIBLE_EXERCISE"))
        val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
        val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
        if (above) { sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }; return generationResult("unsatisfiable", null, null, listOf("SESSION_COUNT_CONFLICT")) }
        current = proposed; evaluation = proposedEvaluation
    }
    // Family target minima when relationships exist.
    while (true) {
        val deficit = evaluation["families"]?.jsonObject?.get("targets")?.jsonObject.orEmpty().mapNotNull { (family, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["plannedSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(family, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rank(candidates.filter { targetContribution(it, "family", deficit.first, database) > 0 }) { targetContribution(it, "family", deficit.first, database) }
        var accepted = false
        for (candidate in ranked) if (!accepted) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Movement-pattern minima.
    while (true) {
        val deficit = evaluation["movementPatterns"]?.jsonObject.orEmpty().mapNotNull { (pattern, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["plannedSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(pattern, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rank(candidates.filter { targetContribution(it, "pattern", deficit.first, database) > 0 }) { targetContribution(it, "pattern", deficit.first, database) }
        var accepted = false
        for (candidate in ranked) if (!accepted) for (slot in sessions.indices.sortedBy { sessions[it].first.size }) if (canAdd(slot, candidate)) {
            val snapshot = sessions.map { it.first.toList() }; add(slot, candidate); val proposed = plan(); val proposedEvaluation = evaluatePlan(proposed, database, p, t, relationships).jsonObject
            val above = proposedEvaluation["muscleCoverage"]?.jsonObject.orEmpty().values.any { it.jsonObject["state"]?.jsonPrimitive?.content == "above_maximum" }
            if (!above) { current = proposed; evaluation = proposedEvaluation; accepted = true; break } else sessions.indices.forEach { sessions[it].first.apply { clear(); addAll(snapshot[it]) } }
        }
        if (!accepted) break
    }
    // Distribute frequency minima across distinct sessions.
    while (true) {
        val deficit = evaluation["frequency"]?.jsonObject.orEmpty().mapNotNull { (muscle, row) -> val value = row.jsonObject; val min = value["minimum"]?.jsonPrimitive?.doubleOrNull; val actual = value["normalizedExposuresPer7Days"]?.jsonPrimitive?.doubleOrNull ?: 0.0; if (min != null && actual < min) Pair(muscle, min - actual) else null }.sortedWith(compareByDescending<Pair<String, Double>> { it.second }.thenBy { it.first }).firstOrNull() ?: break
        val ranked = rank(candidates.filter { targetContribution(it, "frequency", deficit.first, database) > 0 }) { targetContribution(it, "frequency", deficit.first, database) }
        var accepted = false
        for (candidate in ranked) if (!accepted) for (slot in sessions.indices.sortedWith(compareBy<Int> { sessionIndex ->
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
    val finalRationale = current["sessions"]!!.jsonArray.flatMap { it.jsonObject["exercises"]?.jsonArray.orEmpty() }.mapNotNull { it.jsonObject["exerciseId"]?.jsonPrimitive?.content }.distinct().associateWith { id ->
        buildSet { if (id in required) add("REQUIRED_EXERCISE"); if (id in ((p["exercisePreferences"] as? JsonObject)?.get("preferredExerciseIds") as? JsonArray)?.map { it.jsonPrimitive.content }.orEmpty()) add("PREFERRED_EXERCISE"); add("TARGET_COVERAGE") }
    }
    return generationResult(status, current, evaluation, emptyList(), finalRationale, database, p, t, relationships)
}

private fun generationResult(status: String, plan: JsonObject?, evaluation: JsonObject?, constraints: List<String>, rationale: Map<String, Set<String>> = emptyMap(), database: Database? = null, profile: JsonObject? = null, target: JsonObject? = null, relationships: ExerciseRelationships? = null): JsonElement = buildJsonObject {
    val targetRows = mutableListOf<JsonObject>()
    fun collect(rows: JsonObject?, actualKey: String, code: String) = rows.orEmpty().forEach { (id, raw) ->
        val row = raw.jsonObject; val actual = row[actualKey]?.jsonPrimitive?.doubleOrNull ?: 0.0
        row["minimum"]?.jsonPrimitive?.doubleOrNull?.takeIf { actual < it }?.let { minimum -> targetRows += buildJsonObject { put("code", "${code}_UNSATISFIED"); put("targetId", id); put("deficit", minimum - actual) } }
        row["maximum"]?.jsonPrimitive?.doubleOrNull?.takeIf { actual > it }?.let { maximum -> targetRows += buildJsonObject { put("code", "${code}_MAXIMUM_EXCEEDED"); put("targetId", id); put("excess", actual - maximum) } }
    }
    evaluation?.let { value -> collect(value["muscleCoverage"] as? JsonObject, "actualEffectiveSets", "MUSCLE_TARGET"); collect(value["frequency"] as? JsonObject, "normalizedExposuresPer7Days", "FREQUENCY_TARGET"); collect(value["movementPatterns"] as? JsonObject, "plannedSets", "PATTERN_TARGET"); collect(value["families"]?.jsonObject?.get("targets") as? JsonObject, "plannedSets", "FAMILY_TARGET") }
    put("status", status); put("plan", plan ?: JsonNull); put("evaluation", evaluation ?: JsonNull); put("policy", planningPolicyDocument()); put("selectionRationale", buildJsonArray { rationale.toSortedMap().forEach { (id, reasons) -> add(buildJsonObject { put("exerciseId", id); put("reasonCodes", JsonArray(reasons.sorted().map(::JsonPrimitive))) }) } }); put("unsatisfiedConstraints", buildJsonArray { constraints.forEach { add(buildJsonObject { put("code", it) }) } }); put("unsatisfiedTargets", JsonArray(targetRows.sortedWith(compareBy<JsonObject> { it["code"]?.jsonPrimitive?.content ?: "" }.thenBy { it["targetId"]?.jsonPrimitive?.content ?: "" }))); put("unsatisfiedSoftPreferences", JsonArray(emptyList())); put("provenance", buildJsonObject { put("generatorVersion", "0.1.0"); if (evaluation != null && database != null && profile != null && target != null) { put("policyId", "full-body-general-v1"); put("policyVersion", "1"); put("dbSchemaVersion", database.metadata["schemaVersion"] ?: JsonNull); put("dbConverterVersion", database.metadata["converterVersion"] ?: JsonNull); put("dbUpstreamSha256", (database.metadata["upstream"] as? JsonObject)?.get("sha256") ?: JsonNull); put("trainingProfileSchemaVersion", profile["schemaVersion"] ?: JsonNull); put("targetSchemaVersion", target["schemaVersion"] ?: JsonNull); put("trainingStateVersion", JsonNull); put("relationshipSchemaVersion", relationships?.schemaVersion?.let(::JsonPrimitive) ?: JsonNull); put("analysisPolicy", "dbpp-default-volume-v1"); put("setCredits", database.metadata["setCredits"] ?: JsonNull); put("evaluationVersion", evaluation["provenance"]?.jsonObject?.get("analysisVersion") ?: JsonNull); put("currentPlanRevisionId", JsonNull) } })
}

private fun planningPolicyDocument() = buildJsonObject {
    put("policyId", "full-body-general-v1"); put("policyVersion", "1"); put("description", "Reference deterministic full-body construction policy.")
    put("splitStrategy", "full_body_every_session"); put("exerciseSelectionStrategy", "eligible_target_coverage_v1"); put("volumeAllocationStrategy", "greatest_deficit_one_set_v1"); put("frequencyStrategy", "least_exposed_session_v1"); put("tieBreakingStrategy", "explicit_tuple_then_exercise_id_v1")
    put("parameters", buildJsonObject { put("defaultSessionsPerCycle", 3); put("setBlock", 1); put("reps", buildJsonObject { put("min", 6); put("target", 8); put("max", 10) }); put("effort", buildJsonObject { put("rir", 2) }); put("allowUnverifiableEquipment", false); put("preferHistoryContinuity", true); put("avoidSameFamilyInSession", true) })
}
private fun generationInvalid(database: Database, profile: JsonObject, target: JsonObject, errors: List<Pair<String, String>>) = buildJsonObject {
    put("status", "invalid_input"); put("plan", JsonNull); put("evaluation", JsonNull); put("policy", planningPolicyDocument()); put("selectionRationale", JsonArray(emptyList())); put("unsatisfiedConstraints", buildJsonArray { errors.forEach { (code, detail) -> add(buildJsonObject { put("code", code); put("detail", detail) }) } }); put("unsatisfiedTargets", JsonArray(emptyList())); put("unsatisfiedSoftPreferences", JsonArray(emptyList())); put("provenance", buildJsonObject { put("generatorVersion", "0.1.0") })
}
private fun generationConflict(database: Database, profile: JsonObject, target: JsonObject, relationships: ExerciseRelationships?, conflicts: List<Pair<String, String>>) = buildJsonObject {
    put("status", "unsatisfiable"); put("plan", JsonNull); put("evaluation", JsonNull); put("policy", planningPolicyDocument()); put("selectionRationale", JsonArray(emptyList())); put("unsatisfiedConstraints", buildJsonArray { conflicts.forEach { (exercise, detail) -> add(buildJsonObject { put("code", "LOCKED_EXERCISE_CONFLICT"); put("exerciseId", exercise); put("detail", detail) }) } }); put("unsatisfiedTargets", JsonArray(emptyList())); put("unsatisfiedSoftPreferences", JsonArray(emptyList())); put("provenance", buildJsonObject { put("generatorVersion", "0.1.0"); put("policyId", "full-body-general-v1"); put("policyVersion", "1"); put("analysisPolicy", "dbpp-default-volume-v1"); put("dbSchemaVersion", database.metadata["schemaVersion"] ?: JsonNull); put("dbConverterVersion", database.metadata["converterVersion"] ?: JsonNull); put("dbUpstreamSha256", (database.metadata["upstream"] as? JsonObject)?.get("sha256") ?: JsonNull); put("trainingProfileSchemaVersion", profile["schemaVersion"] ?: JsonNull); put("targetSchemaVersion", target["schemaVersion"] ?: JsonNull); put("trainingStateVersion", JsonNull); put("relationshipSchemaVersion", relationships?.schemaVersion?.let(::JsonPrimitive) ?: JsonNull); put("evaluationVersion", JsonNull); put("currentPlanRevisionId", JsonNull); put("setCredits", database.metadata["setCredits"] ?: JsonNull) })
}
