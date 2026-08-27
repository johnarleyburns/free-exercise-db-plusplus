pkg <- file.path("R", "fedbpp.R")
if (file.exists(pkg)) source(pkg) else library(fedbpp)
root <- normalizePath(file.path("..", "..", ".."), mustWork = TRUE)
if (!file.exists(file.path(root, "free-exercise-db-plusplus.json"))) {
  cat("R package check: repository consumer fixtures unavailable; package load passed\n")
  quit(save = "no", status = 0)
}
db <- load_database(file.path(root, "free-exercise-db-plusplus.json"))
stopifnot(length(db$exercises) > 800L)
stopifnot(db$exercises[["Bench_Dips"]]$exerciseId == "Bench_Dips")
w <- list(schemaVersion = "0.2.0", sessionId = "r-test", startTime = "2026-01-01T00:00:00Z", exercises = list(list(exerciseId = "Bench_Dips", order = 1L, sets = list(list(setNumber = 1L, setType = "working", completed = TRUE)))))
validate_workout(w)
totals <- effective_sets(w, db)
stopifnot(nrow(totals) > 0L, all(totals$effective_sets >= 0))
stopifnot(nrow(longitudinal_volume(list(w), db)) > 0L)
relationships <- load_relationships(file.path(root, "exercise-relationships.json"))
stopifnot(family_for(relationships, "Dumbbell_Bench_Press")$familyId == "bench_press")
stopifnot("Barbell_Bench_Press_-_Medium_Grip" %in% family_members(relationships, "bench_press"))
intent <- read_workout_intent(file.path(root, "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json"))
resolution <- resolve_intent(intent, db = db)
stopifnot(resolution$status == "resolved_with_defaults")
stopifnot(resolution$environmentPolicy == "commercial-gym-general-v1")
stopifnot(all(resolution$resolvedProfile$availability$preferredDayOffsets == c(0, 1, 2, 3, 5)))
stopifnot(identical(resolution$explicitOverrides$equipmentAdded, character()))
bad <- intent; bad$requestedGoalPolicy <- "general-strength-v1"
stopifnot(resolve_intent(bad, db = db)$conflicts[[1]]$code == "GOAL_POLICY_MISMATCH")
history_dir <- file.path(root, "fixtures/cross-language/intent/history-aware")
history_intent <- read_workout_intent(file.path(history_dir, "input.json"))
history <- jsonlite::fromJSON(file.path(history_dir, "history.json"), simplifyVector = FALSE)
history_result <- resolve_intent(history_intent, db = db, history = history, as_of = "2026-08-25T12:00:00Z")
stopifnot(identical(history_result$generationOptions$trainingState$activePlan$revisionId, "r1"))
stopifnot(identical(history_result$generationOptions$trainingState$exerciseState[["Barbell_Bench_Press_-_Medium_Grip"]]$recentSessionCount, 1L))
draft <- generate_plan_from_intent(intent, db)
stopifnot(identical(vapply(draft$generation$sessions, `[[`, integer(1), "dayOffset"), as.integer(c(0, 1, 2, 3, 5))))

# Execute every canonical resolution fixture from an installed/source package
# context.  The expected JSON remains the single semantic oracle; this check
# deliberately compares every stable top-level result member.
fixture_root <- file.path(root, "fixtures/cross-language/intent")
for (fixture in sort(list.dirs(fixture_root, full.names = FALSE, recursive = FALSE))) {
  if (file.exists(file.path(fixture_root, fixture, "history.json"))) next
  input <- read_workout_intent(file.path(fixture_root, fixture, "input.json"))
  explicit <- if (file.exists(file.path(fixture_root, fixture, "target.json"))) jsonlite::fromJSON(file.path(fixture_root, fixture, "target.json"), simplifyVector = FALSE) else NULL
  actual <- resolve_intent(input, db = db, target = explicit)
  expected <- jsonlite::fromJSON(file.path(fixture_root, fixture, "expected-resolution.json"), simplifyVector = FALSE)
  stopifnot(identical(actual$status, expected$status))
  stopifnot(identical(actual$defaultsApplied, .strings(expected$defaultsApplied)))
  expected_overrides <- expected$explicitOverrides
  expected_overrides$equipmentAdded <- .strings(expected_overrides$equipmentAdded)
  expected_overrides$equipmentRemoved <- .strings(expected_overrides$equipmentRemoved)
  for (key in names(expected_overrides)) stopifnot(identical(actual$explicitOverrides[[key]], expected_overrides[[key]]))
  stopifnot(identical(actual$planningPolicy, expected$planningPolicy))
  stopifnot(identical(actual$environmentPolicy, expected$environmentPolicy))
  stopifnot(length(actual$conflicts) == length(expected$conflicts))
  if (length(actual$conflicts)) stopifnot(identical(vapply(actual$conflicts, `[[`, character(1), "code"), vapply(expected$conflicts, `[[`, character(1), "code")))
}
cat("R consumer package valid\n")
