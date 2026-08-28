package com.fedbpp

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonPrimitive

internal val JsonElement?.planJsonObjectOrEmpty: JsonObject
    get() = this as? JsonObject ?: JsonObject(emptyMap())
internal fun JsonElement?.planJsonArrayOrEmpty(): JsonArray = this as? JsonArray ?: JsonArray(emptyList())

/** Exact deterministic day-offset selection used by Python's planning.py. */
internal fun canonicalDayOffsets(cycleDays: Int, count: Int, preferred: List<Int>, excluded: Set<Int>, locked: List<Int> = emptyList()): List<Int>? {
    val allowed = (0 until cycleDays).filterNot { it in excluded }
    if (allowed.size < count) return null
    val fixed = locked.distinct().sorted()
    if (fixed.size > count || fixed.any { it !in allowed }) return null
    val chosen = (fixed + preferred.distinct().sorted().filter { it in allowed && it !in fixed }).take(count).toMutableList()
    while (chosen.size < count) {
        val next = allowed.filterNot { it in chosen }.minWithOrNull(compareBy<Int> {
            if (chosen.isEmpty()) -cycleDays else -chosen.minOf { other -> minOf((it - other + cycleDays) % cycleDays, (other - it + cycleDays) % cycleDays) }
        }.thenBy { it }) ?: return null
        chosen += next
    }
    return chosen.sorted()
}

internal data class SessionCountResolution(val counts: List<Int>, val conflicts: List<String>)

/** Python `_session_count`: try target first, then the nearest lower count. */
internal fun canonicalSessionCounts(minimum: Int?, target: Int?, maximum: Int?, defaultCount: Int, policyMinimum: Int = 1): SessionCountResolution {
    if (maximum == 0) return SessionCountResolution(emptyList(), listOf("SESSION_COUNT_CONFLICT"))
    val low = maxOf(1, minimum ?: 1, policyMinimum)
    if (maximum != null && low > maximum) return SessionCountResolution(emptyList(), listOf("SESSION_COUNT_CONFLICT"))
    var desired = target ?: defaultCount
    if (maximum != null && desired > maximum) desired = maximum
    if (desired < low) desired = low
    val upper = maximum ?: maxOf(desired, low)
    return SessionCountResolution((low..upper).sortedWith(compareBy<Int> { kotlin.math.abs(it - desired) }.thenBy { if (it <= desired) 0 else 1 }.thenBy { it }), emptyList())
}

internal data class PlanningCandidate(val exerciseId: String, val familyId: String?, val equipment: String?, val annotation: ExerciseAnnotation)

internal fun targetContribution(candidate: PlanningCandidate, kind: String, key: String, database: Database): Double {
    return when (kind) {
        "muscle" -> {
            val credits = database.metadata["setCredits"] as? JsonObject
            fun credit(role: String, fallback: Double) = credits?.get(role)?.jsonPrimitive?.doubleOrNull ?: fallback
            (if (key in candidate.annotation.direct) credit("direct", 1.0) else 0.0) +
                (if (key in candidate.annotation.indirect) credit("indirect", 0.5) else 0.0) +
                (if (key in candidate.annotation.stabilizers) credit("stabilizer", 0.0) else 0.0)
        }
        "pattern" -> if (key in candidate.annotation.patterns) 1.0 else 0.0
        "family" -> if (candidate.familyId == key) 1.0 else 0.0
        "frequency" -> if (key in candidate.annotation.direct || key in candidate.annotation.indirect) 1.0 else 0.0
        else -> 0.0
    }
}

/** Python planning.py candidate eligibility, with deterministic exerciseId order. */
internal fun canonicalCandidatePool(
    database: Database, profile: JsonObject, relationships: ExerciseRelationships? = null,
    additionalExclusions: Set<String> = emptySet(), allowUnverifiableEquipment: Boolean = false
): List<PlanningCandidate> {
    val constraints = profile["constraints"] as? JsonObject ?: JsonObject(emptyMap())
    val excluded = ((constraints["excludedExerciseIds"] as? JsonArray).orEmpty().map { it.jsonPrimitive.content } + additionalExclusions).toSet()
    val excludedFamilies = (constraints["excludedFamilyIds"] as? JsonArray).orEmpty().map { it.jsonPrimitive.content }.toSet()
    val available = ((profile["equipment"] as? JsonArray).orEmpty().map { it.jsonPrimitive.content }.toMutableSet()).also { if (it.intersect(setOf("bodyweight", "no equipment", "none")).isNotEmpty()) it += "body only" }
    return database.exercises.toSortedMap().mapNotNull { (id, exercise) ->
        val family = relationships?.familyFor(id)?.familyId
        if (id in excluded || family in excludedFamilies || !exercise.annotation.volumeEligible) return@mapNotNull null
        val equipment = exercise.source["equipment"]?.jsonPrimitive?.content
        val compatible = when (equipment) {
            null, "None", "other" -> allowUnverifiableEquipment
            "body only" -> "body only" in available
            else -> equipment in available
        }
        if (!compatible) null else PlanningCandidate(id, family, equipment, exercise.annotation)
    }
}

/** Exact Python rank dimensions for one target deficit, with lexical ID last. */
internal fun rankCandidates(
    candidates: List<PlanningCandidate>, required: Set<String>, existing: Set<String>, history: Map<String, JsonObject> = emptyMap(),
    continuity: String = "preserve", preferred: Set<String> = emptySet(), preferredFamilies: Set<String> = emptySet(),
    avoided: Set<String> = emptySet(), avoidedFamilies: Set<String> = emptySet(), contribution: (PlanningCandidate) -> Double
): List<PlanningCandidate> {
    fun goodHistory(candidate: PlanningCandidate): Boolean {
        val state = history[candidate.exerciseId] ?: return false
        val adherence = ((state["prescriptionAdherence"] as? JsonObject)?.get("setAdherence") as? JsonObject)?.get("fraction")?.jsonPrimitive?.doubleOrNull
        return adherence == null || adherence >= 0.5
    }
    return candidates.sortedWith(Comparator { a, b ->
        val dimensionsA = listOf(
            -if (a.exerciseId in required) 1.0 else 0.0,
            when (continuity) { "preserve" -> -if (a.exerciseId in existing) 1.0 else 0.0; "vary" -> if (a.exerciseId in existing) 1.0 else 0.0; else -> 0.0 },
            when (continuity) { "preserve" -> -if (goodHistory(a)) 1.0 else 0.0; "vary" -> if (goodHistory(a)) 1.0 else 0.0; else -> 0.0 },
            -if (a.exerciseId in preferred) 1.0 else 0.0, -if (a.familyId in preferredFamilies) 1.0 else 0.0,
            -contribution(a), (if (a.exerciseId in avoided) 1.0 else 0.0) + (if (a.familyId in avoidedFamilies) 1.0 else 0.0)
        )
        val dimensionsB = listOf(
            -if (b.exerciseId in required) 1.0 else 0.0,
            when (continuity) { "preserve" -> -if (b.exerciseId in existing) 1.0 else 0.0; "vary" -> if (b.exerciseId in existing) 1.0 else 0.0; else -> 0.0 },
            when (continuity) { "preserve" -> -if (goodHistory(b)) 1.0 else 0.0; "vary" -> if (goodHistory(b)) 1.0 else 0.0; else -> 0.0 },
            -if (b.exerciseId in preferred) 1.0 else 0.0, -if (b.familyId in preferredFamilies) 1.0 else 0.0,
            -contribution(b), (if (b.exerciseId in avoided) 1.0 else 0.0) + (if (b.familyId in avoidedFamilies) 1.0 else 0.0)
        )
        dimensionsA.zip(dimensionsB).firstNotNullOfOrNull { (x, y) -> if (x < y) -1 else if (x > y) 1 else null } ?: a.exerciseId.compareTo(b.exerciseId)
    })
}
