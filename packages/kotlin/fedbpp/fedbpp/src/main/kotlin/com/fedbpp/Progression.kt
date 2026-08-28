package com.fedbpp

import kotlinx.serialization.json.*
import kotlin.math.round

private val countedTypes = setOf("working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted")
private fun JsonElement?.o() = this as? JsonObject ?: JsonObject(emptyMap())
private fun JsonElement?.a() = this as? JsonArray ?: JsonArray(emptyList())
private fun JsonElement?.s() = (this as? JsonPrimitive)?.contentOrNull
private fun JsonElement?.n() = (this as? JsonPrimitive)?.doubleOrNull
private fun clean(x: Double) = round(x * 1_000_000.0) / 1_000_000.0
private fun range(x: JsonElement?): Triple<Double?, Double?, Double?> = when (x) {
    is JsonPrimitive -> Triple(null, x.doubleOrNull, null)
    is JsonObject -> Triple(x["min"]?.n() ?: x["minimumSets"]?.n(), x["target"]?.n() ?: x["targetSets"]?.n(), x["max"]?.n() ?: x["maximumSets"]?.n())
    else -> Triple(null, null, null)
}
private fun policy(id: String) = when (id) {
    "hold-v1" -> buildJsonObject { put("policyId", id); put("policyVersion", "1.0.0"); put("description", "Always retain the supplied prescription."); put("parameters", buildJsonObject { }) }
    "double-progression-v1" -> buildJsonObject { put("policyId", id); put("policyVersion", "1.0.0"); put("description", "Increase a comparable load only after every required working set reaches the top of its rep range at acceptable specified effort."); put("parameters", buildJsonObject { put("loadIncrement", "required for load progression") }) }
    else -> null
}
private fun decision(p: JsonObject, type: String, rx: JsonObject, context: JsonObject, reasons: List<String>, after: JsonObject? = null, evidence: JsonObject = JsonObject(emptyMap())) = buildJsonObject {
    put("schemaVersion", "0.1.0"); put("decisionType", type); put("policyId", p["policyId"]!!); put("policyVersion", p["policyVersion"]!!); put("planId", context["planId"] ?: JsonNull); put("revisionId", context["revisionId"] ?: JsonNull); put("prescriptionId", rx["prescriptionId"] ?: JsonNull); put("exerciseId", rx["exerciseId"] ?: JsonNull)
    put("before", buildJsonObject { listOf("load", "reps", "sets").forEach { if (rx[it] != null) put(it, rx[it]!!) } }); put("after", after ?: buildJsonObject { listOf("load", "reps", "sets").forEach { if (rx[it] != null) put(it, rx[it]!!) } }); put("reasonCodes", buildJsonArray { reasons.distinct().sorted().forEach { add(it) } }); put("evidence", evidence); put("provenance", context["provenance"] ?: buildJsonObject { })
}
fun applyProgressionPolicy(policyId: String, prescription: JsonElement, exerciseState: JsonElement, parameters: JsonElement? = null): JsonElement {
    val p = policy(policyId) ?: throw IllegalArgumentException("unknown progression policy: $policyId")
    val rx = prescription.o(); val state = exerciseState.o(); val context = state["planContext"].o().let { if (it.isEmpty()) buildJsonObject { put("planId", state["planId"] ?: JsonNull); put("revisionId", state["revisionId"] ?: JsonNull) } else it }
    if (policyId == "hold-v1") return decision(p, "hold", rx, context, listOf("POLICY_HOLD"))
    val actual = state["lastActual"].o(); if (actual.isEmpty()) return decision(p, "insufficient_data", rx, context, listOf("NO_RECENT_PERFORMANCE", "NO_MATCHED_ACTUAL"))
    val planned = rx["plannedSets"].a().filter { it.o()["setType"]?.s() in countedTypes }
    val required = if (planned.isNotEmpty()) planned.size else (rx["sets"].n() ?: range(rx["sets"]).second ?: range(rx["sets"]).first ?: 0.0).toInt()
    val sets = actual["sets"].a().filter { it.o()["completed"]?.jsonPrimitive?.booleanOrNull == true && (it.o()["setType"]?.s() == null || it.o()["setType"]?.s() in countedTypes) }
    if (sets.size < required) return decision(p, "hold", rx, context, listOf("SET_TARGET_NOT_COMPLETED", "INCOMPLETE_WORKOUT"), evidence = buildJsonObject { put("plannedSetCount", required); put("actualSetCount", sets.size) })
    val top = range(rx["reps"]).third ?: range(rx["reps"]).second ?: range(rx["reps"]).first
    if (top == null) return decision(p, "insufficient_data", rx, context, listOf("REP_TARGET_NOT_ACHIEVED"), evidence = buildJsonObject { put("sets", JsonArray(sets)) })
    val comparisons = sets.take(required).map { set -> buildJsonObject { put("setId", set.o()["setNumber"] ?: JsonNull); put("plannedReps", rx["reps"] ?: JsonNull); put("actualReps", set.o()["reps"] ?: JsonNull) } }
    if (sets.take(required).any { it.o()["reps"]?.n()?.let { value -> value < top } != false }) return decision(p, "hold", rx, context, listOf("REP_TARGET_NOT_ACHIEVED"), evidence = buildJsonObject { put("sets", JsonArray(comparisons)) })
    val effort = rx["effort"].o(); val effortKey = listOf("rir", "rpe").firstOrNull { effort[it] != null }
    val reasons = mutableListOf("REP_TARGET_ACHIEVED")
    if (effortKey != null) {
        val values = sets.take(required).map { it.o()[effortKey].n() }
        if (values.any { it == null }) return decision(p, "insufficient_data", rx, context, listOf("INSUFFICIENT_EFFORT_DATA"), evidence = buildJsonObject { put("sets", JsonArray(comparisons)); put("effortType", effortKey) })
        val bounds = range(effort[effortKey]); val low = bounds.first ?: bounds.second; val high = bounds.third ?: bounds.second
        val tooLow = values.any { value -> if (effortKey == "rpe") low != null && value!! < low else high != null && value!! > high }
        val tooHigh = values.any { value -> if (effortKey == "rpe") high != null && value!! > high else low != null && value!! < low }
        if (tooLow || tooHigh) return decision(p, "hold", rx, context, buildList { if (tooLow) add("EFFORT_TOO_LOW"); if (tooHigh) add("EFFORT_TOO_HIGH") }, evidence = buildJsonObject { put("sets", JsonArray(comparisons)); put("actualEffort", JsonArray(values.map { it?.let(::JsonPrimitive) ?: JsonNull })) })
        reasons += "EFFORT_WITHIN_TARGET"
    }
    val load = rx["load"].o(); val increment = parameters.o()["loadIncrement"].o()
    val current = load["value"]?.n() ?: load["target"]?.n(); val delta = increment["value"]?.n()
    if (current == null || delta == null || load["unit"]?.s() !in setOf("kg", "lb", "g") || increment["unit"]?.s() !in setOf("kg", "lb", "g")) return decision(p, "insufficient_data", rx, context, listOf("INSUFFICIENT_LOAD_DATA"))
    val units = load["unit"]!!.jsonPrimitive.content; val next = if (units == increment["unit"]!!.jsonPrimitive.content) current + delta else if (units == "kg") current + if (increment["unit"]!!.jsonPrimitive.content == "lb") delta * 0.45359237 else delta / 1000.0 else return decision(p, "insufficient_data", rx, context, listOf("INCOMPATIBLE_LOAD_UNIT"))
    val after = buildJsonObject { rx.forEach { (k, v) -> put(k, v) }; put("load", buildJsonObject { load.forEach { (k, v) -> if (k != "target") put(k, v) }; put("value", clean(next)) }) }
    return decision(p, "increase_load", rx, context, reasons, after = buildJsonObject { listOf("load", "reps", "sets").forEach { if (after[it] != null) put(it, after[it]!!) } }, evidence = buildJsonObject { put("sets", JsonArray(comparisons)); put("previousLoad", rx["load"] ?: JsonNull); put("newLoad", after["load"]!!) })
}
fun suggestProgression(plan: JsonElement, trainingState: JsonElement, policyId: String = "double-progression-v1", parameters: JsonElement? = null): JsonArray {
    val p = plan.o(); val state = trainingState.o(); val active = state["activePlan"].o(); val result = mutableListOf<JsonElement>()
    for (session in p["sessions"].a()) for (rx in session.o()["exercises"].a()) {
        val context = buildJsonObject { put("planId", p["planId"] ?: JsonNull); put("revisionId", p["revisionId"] ?: JsonNull); put("provenance", state["provenance"] ?: buildJsonObject { }) }
        val es = state["exerciseState"].o()[rx.o()["exerciseId"]?.s()].o().toMutableMap(); es["planContext"] = context
        result += if (active["planId"]?.s() == null || active["revisionId"]?.s() == null) decision(policy(policyId)!!, "insufficient_data", rx.o(), context, listOf("NO_ACTIVE_PLAN")) else applyProgressionPolicy(policyId, rx, JsonObject(es), parameters)
    }
    return JsonArray(result)
}
