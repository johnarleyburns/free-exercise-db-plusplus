import com.fedbpp.*
import java.io.File
import kotlinx.serialization.json.Json

private fun requireExample(condition: Boolean, message: String) {
    check(condition) { message }
}

fun main() {
    val repo = File(System.getenv("FEDBPP_REPO") ?: "../../..").canonicalFile
    val input = repo.resolve("fixtures/application-integration/adapt-proposal/request.json")
    val json = Json { ignoreUnknownKeys = true; explicitNulls = true; encodeDefaults = false }
    val persisted = json.decodeFromString<TrainingRequest>(input.readText())
    val history = requireNotNull(persisted.history) { "history is required" }
    val currentPlan = requireNotNull(persisted.currentPlan) { "current plan is required" }
    val profile = requireNotNull(persisted.profile) { "profile is required" }
    val target = requireNotNull(persisted.target) { "target is required" }
    val asOf = java.time.Instant.parse(requireNotNull(persisted.asOf) { "asOf is required" })
    val engine = TrainingEngine.bundled()

    val stateRequest = persisted.copy(
        requestId = "example-derive-state",
        operation = TrainingOperation.DERIVE_STATE,
        history = history,
        target = target,
        currentPlan = null,
        profile = null,
        asOf = asOf.toString(),
        historyWindow = TrainingHistoryWindow.Last28Days
    )
    val stateResult = engine.processTrainingRequest(stateRequest)
    requireExample(stateResult.requestId == stateRequest.requestId, "state requestId was not preserved")
    requireExample(stateResult.status == "state_derived", "state request failed: ${stateResult.status}")
    val state = requireNotNull(stateResult.trainingState) { "state_derived result has no TrainingState" }
    println("state: ${state.subjectId} at ${state.asOf}")

    val progressionResult = engine.processTrainingRequest(
        TrainingRequest(
            requestId = "example-suggest-progression",
            operation = TrainingOperation.SUGGEST_PROGRESSION,
            plan = currentPlan,
            trainingState = state
        )
    )
    when (progressionResult.status) {
        "progression_available" -> println("progression decisions: ${progressionResult.coachDecisions}")
        "insufficient_data" -> println("progression: insufficient_data")
        "invalid", "invalid_input" -> error("progression request failed: ${progressionResult.issues}")
        else -> error("unexpected progression status: ${progressionResult.status}")
    }

    val adaptationRequest = persisted.copy(
        requestId = "example-adapt-plan",
        operation = TrainingOperation.ADAPT_PLAN,
        profile = profile,
        target = target,
        history = history,
        currentPlan = currentPlan,
        asOf = asOf.toString()
    )
    val adaptationResult = engine.processTrainingRequest(adaptationRequest)
    requireExample(adaptationResult.requestId == adaptationRequest.requestId, "adapt requestId was not preserved")
    when (adaptationResult.status) {
        "no_change" -> println("adaptation: no_change")
        "revision_proposed", "regeneration_proposed" -> {
            val proposal = requireNotNull(adaptationResult.adaptation) { "proposal is missing" }
            requireNotNull(proposal.proposedPlan) { "proposed PLAN is missing" }
            println("adaptation: ${adaptationResult.status}")
            println("coach decisions: ${proposal.decisions}")
            println("proposed PLAN: ${proposal.proposedPlan}")
        }
        "insufficient_data" -> println("adaptation: insufficient_data")
        "invalid", "invalid_input", "unsatisfiable" -> error("adaptation failed: ${adaptationResult.issues}")
        else -> error("unexpected adaptation status: ${adaptationResult.status}")
    }
    println("DB++ proposes only; the host app reviews, persists, approves, and activates revisions.")
}
