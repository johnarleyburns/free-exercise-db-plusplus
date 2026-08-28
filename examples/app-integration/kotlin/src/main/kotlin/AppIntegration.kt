import com.fedbpp.TrainingEngine
import com.fedbpp.TrainingOperation
import com.fedbpp.TrainingRequest
import com.fedbpp.processTrainingRequest
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

fun main() {
val engine = TrainingEngine.bundled()
val intent = com.fedbpp.WorkoutIntent(
    goal = "hypertrophy", environment = "commercial_gym",
    schedule = com.fedbpp.WorkoutSchedule(
        cycleLengthDays = 7,
        sessionsPerCycle = com.fedbpp.IntRangeValue(target = 5),
        preferredWeekdays = listOf("monday", "tuesday", "wednesday", "thursday", "saturday")
    ),
    sessionConstraints = com.fedbpp.SessionConstraints(
        exercisesPerSession = com.fedbpp.IntRangeValue(min = 3, max = 4)
    ), useHistory = true, historyWindow = "last_28_days"
)
val request = TrainingRequest(requestId = "demo-generate", operation = TrainingOperation.GENERATE_FROM_INTENT,
    intent = intent, asOf = "2026-08-28T12:00:00Z")
val result = engine.processTrainingRequest(request)
when (result.status) {
    "needs_clarification" -> println(result.missingInformation)
    "generated", "generated_with_target_gaps" -> println(result.plan)
    "invalid", "unsatisfiable" -> println(result.issues)
    else -> println(result.status)
}
}
