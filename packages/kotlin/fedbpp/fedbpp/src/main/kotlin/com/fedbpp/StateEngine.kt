package com.fedbpp

import java.time.Instant
import java.time.ZoneId
import java.time.ZoneOffset
import kotlinx.serialization.json.*

private fun JsonElement?.stObj() = this as? JsonObject ?: JsonObject(emptyMap())
private fun JsonElement?.stArr() = this as? JsonArray ?: JsonArray(emptyList())
private fun JsonElement?.stStr() = (this as? JsonPrimitive)?.contentOrNull
private fun stInstant(s: String?) = s?.let { runCatching { Instant.parse(it) }.getOrNull() }
private val stTypes = setOf("working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted")
private fun stCompleted(x: JsonObject) = x["sets"].stArr().map { it.stObj() }.filter { it["completed"]?.jsonPrimitive?.booleanOrNull == true && (it["setType"].stStr() == null || it["setType"].stStr() in stTypes) }
private fun stClean(value: JsonElement): JsonElement = when (value) {
    is JsonObject -> JsonObject(value.filter { (_, item) -> item !is JsonNull && (item !is JsonObject || item.jsonObject.isNotEmpty()) }.filterKeys { it != "extensions" && it != "notes" && !(it == "laterality" && value[it]?.jsonPrimitive?.contentOrNull == "unspecified") }.mapValues { stClean(it.value) })
    is JsonArray -> JsonArray(value.map(::stClean))
    else -> value
}
private fun stSets(x: JsonObject) = x["plannedSets"].stArr().size.takeIf { it > 0 }?.toDouble() ?: x["sets"]?.jsonPrimitive?.doubleOrNull ?: x["sets"].stObj()["target"]?.jsonPrimitive?.doubleOrNull ?: x["sets"].stObj()["min"]?.jsonPrimitive?.doubleOrNull ?: 0.0
private fun JsonElement?.evRangeTriple(): Triple<Double, Double, Double> = when (this) {
    is JsonPrimitive -> doubleOrNull?.let { Triple(it, it, it) } ?: Triple(0.0, 0.0, 0.0)
    is JsonObject -> Triple(this["min"]?.jsonPrimitive?.doubleOrNull ?: this["minimumSets"]?.jsonPrimitive?.doubleOrNull ?: 0.0, this["target"]?.jsonPrimitive?.doubleOrNull ?: this["targetSets"]?.jsonPrimitive?.doubleOrNull ?: this["min"]?.jsonPrimitive?.doubleOrNull ?: 0.0, this["max"]?.jsonPrimitive?.doubleOrNull ?: this["maximumSets"]?.jsonPrimitive?.doubleOrNull ?: this["target"]?.jsonPrimitive?.doubleOrNull ?: this["min"]?.jsonPrimitive?.doubleOrNull ?: 0.0)
    else -> Triple(0.0, 0.0, 0.0)
}

fun deriveTrainingStateCanonical(history: JsonElement, asOf: Instant, window: TrainingHistoryWindow, database: Database?, relationships: ExerciseRelationships?, target: JsonElement? = null, canonicalAsOf: String? = null): JsonElement {
    val root = history.stObj(); val targetWasExplicit = target != null
    val effectiveTarget = target ?: root["targets"].stArr().lastOrNull()
    val plans = root["plans"].stArr().map { it.stObj() }
    val activations = root["planActivations"].stArr().map { it.stObj() }
    val activeCandidates = activations.mapNotNull { a ->
        val from = stInstant(a["effectiveFrom"].stStr()) ?: return@mapNotNull null
        val to = stInstant(a["effectiveTo"].stStr())
        if (from <= asOf && (to == null || asOf < to)) plans.firstOrNull { it["planId"] == a["planId"] && it["revisionId"] == a["revisionId"] }?.let { Triple(it, from, a) } else null
    }
    val active = activeCandidates.maxByOrNull { it.second }
    val zone = ZoneId.of(root["timezone"]?.jsonPrimitive?.contentOrNull ?: "UTC")
    val asDate = asOf.atZone(zone).toLocalDate()
    val (start, end, type) = when (window) {
        TrainingHistoryWindow.Last7Days -> Triple(asDate.minusDays(6), asDate, "last_7_days")
        TrainingHistoryWindow.Last28Days -> Triple(asDate.minusDays(27), asDate, "last_28_days")
        is TrainingHistoryWindow.Custom -> Triple(java.time.LocalDate.parse(window.start.take(10)), minOf(java.time.LocalDate.parse(window.end.take(10)), asDate), "custom_date_range")
        else -> {
            val cycle = active?.first?.get("cycle").stObj()["lengthDays"]?.jsonPrimitive?.intOrNull ?: 7
            val anchor = active?.second?.atZone(zone)?.toLocalDate() ?: asDate
            val elapsed = java.time.temporal.ChronoUnit.DAYS.between(anchor, asDate).coerceAtLeast(0)
            val s = anchor.plusDays((elapsed / cycle) * cycle)
            Triple(s, minOf(s.plusDays(cycle - 1L), asDate), if (window is TrainingHistoryWindow.CurrentPhase) "current_phase" else "current_plan_cycle")
        }
    }
    val workouts = root["workouts"].stArr().map { it.stObj() }.filter { val t = stInstant(it["startTime"].stStr()); t != null && t.atZone(zone).toLocalDate() >= start && t.atZone(zone).toLocalDate() <= asDate }
    val stateWorkouts = workouts.filter { stInstant(it["startTime"].stStr())?.let { timestamp -> timestamp <= asOf } == true }
    val canonicalAsOf = canonicalAsOf ?: root["asOf"]?.jsonPrimitive?.contentOrNull ?: (asOf.toString().removeSuffix("Z") + "+00:00"); val periodStart = start.toString(); val periodEnd = end.toString()
    val sessionRows = mutableListOf<JsonObject>(); val historyExerciseRows = mutableListOf<JsonObject>(); val consumedWorkouts = mutableSetOf<String>()
    val directActual = sortedMapOf<String, Double>(); val indirectActual = sortedMapOf<String, Double>(); val stabilizerActual = sortedMapOf<String, Double>(); val exposureActual = sortedMapOf<String, Double>()
    fun countedSets(exercise: JsonObject): List<JsonObject> = stCompleted(exercise)
    fun plannedRange(rx: JsonObject): Triple<Double, Double, Double> {
        val planned = rx["plannedSets"].stArr().filter { it.stObj()["setType"].stStr() in stTypes }.size.toDouble()
        return if (planned > 0) Triple(planned, planned, planned) else rx["sets"].evRangeTriple()
    }
    fun addActual(exercise: JsonObject) {
        val count = countedSets(exercise).size.toDouble(); val id = exercise["exerciseId"].stStr(); val annotation = id?.let { database?.exercises?.get(it)?.annotation }
        if (annotation == null) return
        annotation.direct.forEach { directActual[it] = (directActual[it] ?: 0.0) + count }; annotation.indirect.forEach { indirectActual[it] = (indirectActual[it] ?: 0.0) + count }; annotation.stabilizers.forEach { stabilizerActual[it] = (stabilizerActual[it] ?: 0.0) + count }
        (annotation.direct + annotation.indirect).distinct().forEach { exposureActual[it] = (exposureActual[it] ?: 0.0) + 1.0 }
    }
    fun exerciseRow(rx: JsonObject?, actual: JsonObject?, status: String, sessionId: String?): JsonObject {
        val range = rx?.let(::plannedRange) ?: Triple(0.0, 0.0, 0.0); val sets = actual?.let { countedSets(it).size } ?: 0
        if (status == "unplanned_addition") return buildJsonObject { put("subject_id", root["subjectId"] ?: JsonNull); put("period", periodStart); put("session_id", sessionId?.let(::JsonPrimitive) ?: JsonNull); put("prescription_id", JsonNull); put("planned_exercise_id", JsonNull); put("actual_exercise_id", actual?.get("exerciseId") ?: JsonNull); put("match_status", status); put("actual_sets", sets); put("unmapped", database != null && database.exercises.containsKey(actual?.get("exerciseId")?.stStr()).not()) }
        return buildJsonObject { put("subject_id", root["subjectId"] ?: JsonNull); put("period", periodStart); put("session_id", sessionId?.let(::JsonPrimitive) ?: JsonNull); put("prescription_id", rx?.get("prescriptionId") ?: JsonNull); put("planned_exercise_id", rx?.get("exerciseId") ?: JsonNull); put("actual_exercise_id", actual?.get("exerciseId") ?: JsonNull); put("match_status", status); put("planned_sets_min", range.first); put("planned_sets_target", range.second); put("planned_sets_max", range.third); put("actual_sets", sets); put("reps_adherence", JsonNull); put("load_adherence", JsonNull); put("rpe_adherence", JsonNull); put("rir_adherence", JsonNull); put("set_adherence", JsonNull); put("volume_load_adherence", JsonNull); put("substitution_reason", actual?.get("substitution").stObj()["reason"] ?: JsonNull); if (status == "unplanned_addition") put("unmapped", database?.exercises?.containsKey(actual?.get("exerciseId")?.stStr()) != true) }
    }
    fun sessionRow(status: String, scheduledDate: java.time.LocalDate?, workout: JsonObject?, session: JsonObject?, plan: JsonObject?): JsonObject {
        val ranges = session?.get("exercises").stArr().map { value -> plannedRange(value.stObj()) }; val min = ranges.fold(0.0) { total, value -> total + value.first }; val targetValue = ranges.fold(0.0) { total, value -> total + value.second }; val max = ranges.fold(0.0) { total, value -> total + value.third }; val counted = workout?.get("exercises").stArr()?.sumOf { countedSets(it.stObj()).size } ?: 0
        val adherence: JsonElement = if (status == "matched") JsonPrimitive(1.0) else if (status == "missed_planned_session") JsonPrimitive(0.0) else JsonNull
        return buildJsonObject { put("subject_id", root["subjectId"] ?: JsonNull); put("period_type", "custom_date_range"); put("period_start", periodStart); put("period_end", periodEnd); put("scheduled_date", scheduledDate?.toString()?.let(::JsonPrimitive) ?: JsonNull); put("session_id", workout?.get("sessionId") ?: JsonNull); put("timestamp", workout?.get("startTime") ?: JsonNull); put("plan_id", plan?.get("planId") ?: active?.first?.get("planId") ?: JsonNull); put("revision_id", plan?.get("revisionId") ?: active?.first?.get("revisionId") ?: JsonNull); put("plan_session_id", session?.get("planSessionId") ?: JsonNull); put("session_status", status); put("planned_exercises", session?.get("exercises").stArr().size); put("matched_exercises", if (status == "matched") session?.get("exercises").stArr().size else 0); put("substitutions", 0); put("unplanned_exercises", if (status == "unplanned_session") (workout?.get("exercises").stArr().size ?: 0) else 0); put("planned_sets", targetValue); put("planned_set_min", min); put("planned_set_max", max); put("actual_counted_sets", counted); put("missing_prescriptions", if (status == "missed_planned_session" || status == "unplanned_session") (session?.get("exercises").stArr().size ?: 0) else 0); put("missed_sets", if (status == "missed_planned_session") targetValue else 0.0); put("missed_sets_min", if (status == "missed_planned_session") min else 0.0); put("missed_sets_target", if (status == "missed_planned_session") targetValue else 0.0); put("missed_sets_max", if (status == "missed_planned_session") max else 0.0); put("unplanned_sets", if (status == "unplanned_session") counted else 0); put("session_adherence", adherence) }
    }
    if (active != null) {
        val plan = active.first; val anchor = active.second.atZone(zone).toLocalDate(); val cycle = plan["cycle"].stObj()["lengthDays"]?.jsonPrimitive?.intOrNull ?: 7; var cycleStart = anchor.plusDays((java.time.temporal.ChronoUnit.DAYS.between(anchor, start).floorDiv(cycle)) * cycle.toLong())
        while (!cycleStart.isAfter(end)) {
            plan["sessions"].stArr().forEach { sv -> val session = sv.stObj(); val date = cycleStart.plusDays(session["dayOffset"]?.jsonPrimitive?.intOrNull?.toLong() ?: 0); if (date !in start..end) return@forEach
                val workout = workouts.firstOrNull { w -> w["sessionId"].stStr() !in consumedWorkouts && stInstant(w["startTime"].stStr())?.atZone(zone)?.toLocalDate() == date && (w["planReference"].stObj()["planSessionId"].stStr() == null || w["planReference"].stObj()["planSessionId"].stStr() == session["planSessionId"].stStr()) && (w["planReference"].stObj()["revisionId"].stStr() == null || w["planReference"].stObj()["revisionId"].stStr() == plan["revisionId"].stStr()) }
                if (workout == null) { sessionRows += sessionRow("missed_planned_session", date, null, session, plan); session["exercises"].stArr().forEach { historyExerciseRows += exerciseRow(it.stObj(), null, "missing_prescription", null) } }
                else { consumedWorkouts += workout["sessionId"].stStr().orEmpty(); sessionRows += sessionRow("matched", date, workout, session, plan); workout["exercises"].stArr().forEach { val actual = it.stObj(); val substitution = actual["substitution"].stObj(); val plannedId = actual["exercisePrescriptionId"]?.stStr() ?: substitution["plannedPrescriptionId"]?.stStr(); val rx = session["exercises"].stArr().map { it.stObj() }.firstOrNull { it["prescriptionId"]?.stStr() == plannedId || it["exerciseId"] == actual["exerciseId"] }; val status = if (substitution.isNotEmpty() && rx != null) "substitution" else if (rx == null) "unplanned_addition" else "matched"; historyExerciseRows += exerciseRow(rx, actual, status, workout["sessionId"].stStr()); addActual(actual) } }
            }
            cycleStart = cycleStart.plusDays(cycle.toLong())
        }
    }
    workouts.filter { it["sessionId"].stStr() !in consumedWorkouts }.forEach { workout ->
        val referencedSession = active?.first?.get("sessions").stArr().map { it.stObj() }.firstOrNull { it["planSessionId"].stStr() == workout["planReference"].stObj()["planSessionId"].stStr() }
        sessionRows += sessionRow("unplanned_session", null, workout, referencedSession, active?.first); workout["exercises"].stArr().forEach { actual -> historyExerciseRows += exerciseRow(null, actual.stObj(), "unplanned_addition", workout["sessionId"].stStr()); addActual(actual.stObj()) }
    }
    val ids = sortedSetOf<String>()
    active?.first?.get("sessions").stArr().forEach { it.stObj()["exercises"].stArr().forEach { it.stObj()["exerciseId"].stStr()?.let(ids::add) } }
    stateWorkouts.forEach { it["exercises"].stArr().forEach { it.stObj()["exerciseId"].stStr()?.let(ids::add) } }
    val exerciseStateRows = buildJsonObject {
        ids.forEach { id ->
            val observations = stateWorkouts.flatMap { w -> w["exercises"].stArr().map { w to it.stObj() }.filter { it.second["exerciseId"].stStr() == id } }.sortedWith(compareBy({ stInstant(it.first["startTime"].stStr()) }, { it.first["sessionId"].stStr() }))
            val actual = observations.lastOrNull()?.second?.let { stCompleted(it).map(::stClean) } ?: emptyList()
            val allSets = observations.flatMap { stCompleted(it.second) }
            val prescribed = active?.first?.get("sessions").stArr().flatMap { it.stObj()["exercises"].stArr() }.map { it.stObj() }.firstOrNull { it["exerciseId"].stStr() == id }
            val performance = buildJsonArray { observations.forEach { (w, e) -> add(buildJsonObject { put("sessionId", w["sessionId"] ?: JsonNull); put("timestamp", w["startTime"] ?: JsonNull); put("exerciseId", id); put("exercisePrescriptionId", e["exercisePrescriptionId"] ?: JsonNull); put("sets", buildJsonArray { stCompleted(e).map(::stClean).forEach(::add) }) }) } }
            val rows = historyExerciseRows.filter { it["planned_exercise_id"].stStr() == id || it["actual_exercise_id"].stStr() == id }
            fun summary(forPrescription: String? = null): JsonObject { val selected = rows.filter { forPrescription == null || it["prescription_id"].stStr() == forPrescription }; val missing = selected.count { it["match_status"].stStr() == "missing_prescription" }; val matched = selected.count { it["match_status"].stStr() == "matched" }; val substitutions = selected.count { it["match_status"].stStr() == "substitution" }; val plannedSets = selected.sumOf { it["planned_sets_target"]?.jsonPrimitive?.doubleOrNull ?: 0.0 }; val actualSets = selected.sumOf { it["actual_sets"]?.jsonPrimitive?.doubleOrNull ?: 0.0 }; return buildJsonObject { put("matchedOccurrences", matched); put("missingOccurrences", missing); put("substitutionOccurrences", substitutions); put("plannedSets", plannedSets); put("actualSets", actualSets); put("setAdherence", JsonNull); put("repsAdherence", JsonNull); put("loadAdherence", JsonNull); put("rpeAdherence", JsonNull); put("rirAdherence", JsonNull) } }
            val prescriptions = active?.first?.get("sessions").stArr().flatMap { it.stObj()["exercises"].stArr() }.map { it.stObj() }.filter { it["exerciseId"].stStr() == id && it["prescriptionId"].stStr() != null }
            put(id, buildJsonObject { put("exerciseId", id); put("lastPerformedAt", observations.lastOrNull()?.first?.get("startTime") ?: JsonNull); put("lastPrescription", prescribed ?: JsonNull); put("lastActual", if (observations.isEmpty()) JsonNull else buildJsonObject { put("exerciseId", id); put("sets", buildJsonArray { actual.forEach(::add) }) }); put("latestPerformance", performance.lastOrNull() ?: JsonNull); put("recentPerformances", performance); put("recentSessionCount", JsonPrimitive(observations.size)); put("recentCompletedSetCount", JsonPrimitive(allSets.size)); put("recentReps", buildJsonArray { actual.mapNotNull { it.jsonObject["reps"] }.forEach(::add) }); put("recentLoads", buildJsonArray { actual.mapNotNull { it.jsonObject["load"] }.forEach(::add) }); put("recentRPE", buildJsonArray { actual.mapNotNull { it.jsonObject["rpe"] }.forEach(::add) }); put("recentRIR", buildJsonArray { actual.mapNotNull { it.jsonObject["rir"] }.forEach(::add) }); put("recentSetTypes", buildJsonArray { actual.mapNotNull { it.jsonObject["setType"] }.forEach(::add) }); put("substitutionCount", JsonPrimitive(observations.count { it.second["substitution"] !is JsonNull && it.second["substitution"] != null })); put("unplannedCount", JsonPrimitive(observations.count { it.second["exercisePrescriptionId"].stStr() == null })); put("prescriptionAdherence", summary()); put("prescriptionAdherenceByPrescriptionId", buildJsonObject { prescriptions.forEach { rx -> put(rx["prescriptionId"].stStr()!!, summary(rx["prescriptionId"].stStr())) } }) })
        }
    }
    val activeRow = buildJsonObject {
        active?.let { (plan, from) ->
            val cycle = plan["cycle"].stObj()["lengthDays"]?.jsonPrimitive?.intOrNull ?: 7
            // Cycle position follows the activation instant's canonical UTC
            // date; scheduled occurrences use the history/analyzer timezone.
            val position = (java.time.temporal.ChronoUnit.DAYS.between(from.atZone(ZoneOffset.UTC).toLocalDate(), asDate).coerceAtLeast(0) % cycle) + 1
            put("planId", plan["planId"] ?: JsonNull); put("revisionId", plan["revisionId"] ?: JsonNull); put("phaseId", JsonNull); put("cyclePosition", JsonPrimitive(position))
            val nextAnchor = from.atZone(zone).toLocalDate().let { var d = it; while (!d.isAfter(asDate)) d = d.plusDays(cycle.toLong()); d }
            val next = plan["sessions"].stArr().map { it.stObj() }.minByOrNull { nextAnchor.plusDays(it["dayOffset"]?.jsonPrimitive?.intOrNull?.toLong() ?: 0) }
            put("nextScheduledOccurrence", next?.let { buildJsonObject { put("planSessionId", it["planSessionId"] ?: JsonNull); put("scheduledDate", nextAnchor.plusDays(it["dayOffset"]?.jsonPrimitive?.intOrNull?.toLong() ?: 0).toString()) } } ?: JsonNull)
        }
    }
    val window = buildJsonObject { put("type", type); put("start", start.toString()); put("end", end.toString()) }
    val skipped = historyExerciseRows.filter { it["match_status"].stStr() == "missing_prescription" }.groupingBy { it["prescription_id"].stStr().orEmpty() }.eachCount().filterKeys { it.isNotEmpty() }.toSortedMap(); val substitutions = historyExerciseRows.filter { it["match_status"].stStr() == "substitution" }.groupingBy { it["prescription_id"].stStr().orEmpty() }.eachCount().filterKeys { it.isNotEmpty() }.toSortedMap()
    val substitutionHistoryData = sortedMapOf<String, MutableMap<String, MutableList<JsonElement>>>()
    workouts.forEach { workout -> workout["exercises"].stArr().forEach { exercise -> val sub = exercise.stObj()["substitution"].stObj(); val pid = sub["plannedPrescriptionId"].stStr(); val replacement = exercise.stObj()["exerciseId"].stStr(); if (pid != null && replacement != null) { val row = substitutionHistoryData.getOrPut(pid) { sortedMapOf() }.getOrPut(replacement) { mutableListOf(JsonPrimitive(0), JsonArray(emptyList()), JsonArray(emptyList())) }; row[0] = JsonPrimitive((row[0].jsonPrimitive.intOrNull ?: 0) + 1); (row[1] as JsonArray).toMutableList().also { it += workout["sessionId"] ?: JsonNull; row[1] = JsonArray(it) }; (row[2] as JsonArray).toMutableList().also { it += workout["startTime"] ?: JsonNull; row[2] = JsonArray(it) } } } }
    val substitutionHistory = buildJsonObject { substitutionHistoryData.forEach { (pid, replacements) -> put(pid, buildJsonObject { replacements.forEach { (replacement, row) -> put(replacement, buildJsonObject { put("count", row[0]); put("sessionIds", row[1]); put("timestamps", row[2]) }) } }) } }
    val targetMuscles = (effectiveTarget as? JsonObject)?.get("muscles").stObj(); val targetCharacterKeys = targetMuscles.keys.flatMap { it.toList().map(Char::toString) }.toSet(); val muscleKeys = (directActual.keys + indirectActual.keys + stabilizerActual.keys + targetCharacterKeys).toSortedSet(); val credits = database?.metadata?.get("setCredits").stObj(); val directCredit = credits["direct"]?.jsonPrimitive?.doubleOrNull ?: 1.0; val indirectCredit = credits["indirect"]?.jsonPrimitive?.doubleOrNull ?: 0.5; val stabilizerCredit = credits["stabilizer"]?.jsonPrimitive?.doubleOrNull ?: 0.0
    val plannedEffective = sortedMapOf<String, Double>(); val scheduledCount = sessionRows.count { it["scheduled_date"] !is JsonNull }; active?.first?.get("sessions").stArr().forEach { session -> session.stObj()["exercises"].stArr().forEach { rx -> val count = scheduledCount.toDouble() * stSets(rx.stObj()); val annotation = rx.stObj()["exerciseId"].stStr()?.let { database?.exercises?.get(it)?.annotation }; if (annotation != null) { annotation.direct.forEach { plannedEffective[it] = (plannedEffective[it] ?: 0.0) + count * directCredit }; annotation.indirect.forEach { plannedEffective[it] = (plannedEffective[it] ?: 0.0) + count * indirectCredit }; annotation.stabilizers.forEach { plannedEffective[it] = (plannedEffective[it] ?: 0.0) + count * stabilizerCredit } } } }
    fun targetState(actual: Double, raw: JsonElement?): String { val r = raw.evRangeTriple(); return when { raw == null -> "not_targeted"; root["targets"].stArr().isNotEmpty() && targetWasExplicit -> "within_range_below_target"; actual < r.first -> "below_minimum"; actual > r.third -> "above_maximum"; actual < r.second -> "within_range_below_target"; actual > r.second -> "within_range_above_target"; else -> "at_target" } }
    val muscleRows = buildJsonObject { muscleKeys.forEach { id -> val d = directActual[id] ?: 0.0; val i = indirectActual[id] ?: 0.0; val s = stabilizerActual[id] ?: 0.0; val effective = d * directCredit + i * indirectCredit + s * stabilizerCredit; put(id, buildJsonObject { put("muscleId", id); put("directSets", d); put("indirectSets", i); put("stabilizerSets", s); put("effectiveSets", effective); put("exposures", exposureActual[id] ?: 0.0); put("mappedFraction", 1.0); if (targetWasExplicit) { put("targetState", targetState(effective, targetMuscles[id])); put("plannedVsActual", buildJsonObject { put("planned", plannedEffective[id] ?: 0.0); put("actual", effective) }) } }) } }
    val familyRows = buildJsonObject {
        if (relationships != null) {
            val familiesSeen = mutableSetOf<String>()
            ids.forEach { id ->
                relationships.familyFor(id)?.familyId?.let { family ->
                    if (familiesSeen.add(family)) {
                        val familyIds = ids.filter { candidate -> relationships.familyFor(candidate)?.familyId == family }
                        val mostRecent = familyIds.maxByOrNull { candidate ->
                            stateWorkouts.filter { workout -> workout["exercises"].stArr().any { it.stObj()["exerciseId"].stStr() == candidate } }
                                .maxOfOrNull { stInstant(it["startTime"].stStr()) ?: Instant.MIN } ?: Instant.MIN
                        } ?: id
                        put(family, buildJsonObject {
                            put("familyId", family)
                            put("recentExerciseIds", buildJsonArray { familyIds.forEach(::add) })
                            put("mostRecentExerciseId", mostRecent)
                            put("explicitSubstitutionCount", substitutionHistoryData.values.flatMap { it.values }.sumOf { it[0].jsonPrimitive.intOrNull ?: 0 })
                            put("variantHistory", buildJsonArray { })
                        })
                    }
                }
            }
        }
    }
    val orderedSessions = sessionRows.sortedBy { it["scheduled_date"].stStr() ?: "9999-99-99" }
    val adherence = buildJsonObject { put("sessionAdherence", JsonArray(orderedSessions)); put("exercisePrescriptionAdherence", JsonArray(historyExerciseRows.sortedWith(compareBy({ it["session_id"].stStr() ?: "" }, { it["prescription_id"].stStr() ?: "" })))); put("missedScheduledOccurrences", JsonArray(orderedSessions.filter { it["session_status"].stStr() == "missed_planned_session" })); put("repeatedSkippedExercises", JsonArray(skipped.filterValues { it > 1 }.keys.map(::JsonPrimitive))); put("repeatedSubstitutions", JsonArray(substitutions.filterValues { it > 1 }.keys.map(::JsonPrimitive))); put("skippedPrescriptionCounts", buildJsonObject { skipped.forEach { (key, value) -> put(key, value) } }); put("substitutionCountsByPrescription", buildJsonObject { substitutions.forEach { (key, value) -> put(key, value) } }); put("substitutionHistoryByPrescription", substitutionHistory); put("unplannedExercises", JsonArray(historyExerciseRows.filter { it["match_status"].stStr() == "unplanned_addition" }.sortedBy { it["session_id"].stStr() ?: "" })); put("unplannedSets", historyExerciseRows.filter { it["match_status"].stStr() == "unplanned_addition" }.sumOf { it["actual_sets"]?.jsonPrimitive?.intOrNull ?: 0 }); put("substitutionAdjustedCompletion", historyExerciseRows.count { it["match_status"].stStr() in setOf("matched", "substitution") }) }
    val provenance = buildJsonObject { put("stateVersion", "0.1.0"); put("analysisVersion", "1.4.1"); put("analysisPolicy", "dbpp-default-volume-v1"); put("asOf", canonicalAsOf); put("timezone", zone.id); put("historyWindow", window); put("dbSchemaVersion", database?.metadata?.get("schemaVersion") ?: JsonNull); put("dbConverterVersion", database?.metadata?.get("converterVersion") ?: JsonNull); put("dbUpstreamSha256", database?.metadata?.get("upstream").stObj()["sha256"] ?: JsonNull); put("relationshipSchemaVersion", relationships?.schemaVersion?.let(::JsonPrimitive) ?: JsonNull); put("workoutCount", JsonPrimitive(workouts.size)); put("mappedFraction", JsonNull); put("setCredits", buildJsonObject { put("direct", directCredit); put("indirect", indirectCredit); put("stabilizer", stabilizerCredit) }); put("planSchemaVersions", JsonArray(plans.mapNotNull { it["schemaVersion"].stStr() }.distinct().sorted().map(::JsonPrimitive))); put("workoutSchemaVersions", JsonArray(workouts.mapNotNull { it["schemaVersion"].stStr() }.distinct().sorted().map(::JsonPrimitive))); put("targetSchemaVersion", (target as? JsonObject)?.get("schemaVersion") ?: JsonNull) }
    return buildJsonObject { put("stateVersion", "0.1.0"); put("subjectId", root["subjectId"] ?: JsonNull); put("asOf", canonicalAsOf); put("historyWindow", window); put("activePlan", activeRow); put("exerciseState", exerciseStateRows); put("familyState", familyRows); put("muscleState", muscleRows); put("adherenceState", adherence); put("sessionState", JsonArray(orderedSessions)); put("provenance", provenance) }
}
