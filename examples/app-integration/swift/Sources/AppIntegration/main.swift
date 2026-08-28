import FreeExerciseDBPlusPlus

let engine = try TrainingEngine.bundled()
let intent = WorkoutIntent(
  intentId: "demo-intent", subjectId: "user-123", goal: "hypertrophy",
  environment: "commercial_gym",
  schedule: WorkoutSchedule(cycleLengthDays: 7,
    sessionsPerCycle: IntRange(target: 5),
    preferredWeekdays: ["monday", "tuesday", "wednesday", "thursday", "saturday"]),
  sessionConstraints: SessionConstraints(exercisesPerSession: IntRange(min: 3, max: 4)),
  useHistory: true, historyWindow: "last_28_days")
let request = TrainingRequest(requestId: "demo-generate",
                              operation: .generateFromIntent, intent: intent,
                              asOf: "2026-08-28T12:00:00Z")
let result = try engine.processTrainingRequest(request)
switch result.status {
case "needs_clarification": print(result.missingInformation)
case "generated", "generated_with_target_gaps": print(result.plan as Any)
case "invalid", "unsatisfiable": print(result.issues)
default: print(result.status)
}
