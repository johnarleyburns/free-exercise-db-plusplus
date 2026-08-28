library(fedbpp)

db <- load_database()
relationships <- load_relationships()
intent <- list(
  schemaVersion = "0.1.0", intentId = "demo-intent", subjectId = "user-123",
  goal = "hypertrophy", environment = "commercial_gym",
  schedule = list(cycleLengthDays = 7L, sessionsPerCycle = list(target = 5L),
                  preferredWeekdays = c("monday", "tuesday", "wednesday", "thursday", "saturday")),
  sessionConstraints = list(exercisesPerSession = list(min = 3L, max = 4L)),
  useHistory = TRUE, historyWindow = "last_28_days"
)
request <- list(schemaVersion = "0.1.0", requestId = "demo-generate",
                operation = "generate_from_intent", intent = intent,
                asOf = "2026-08-28T12:00:00Z")
result <- process_training_request(request, db, relationships)
print(result$status)
