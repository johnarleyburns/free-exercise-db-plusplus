library(fedbpp)

repo <- normalizePath(Sys.getenv("FEDBPP_REPO", getwd()), mustWork = TRUE)
read_doc <- function(path) jsonlite::fromJSON(path, simplifyVector = FALSE,
                                               simplifyDataFrame = FALSE,
                                               simplifyMatrix = FALSE)
source <- read_doc(file.path(repo, "fixtures", "application-integration",
                             "adapt-proposal", "request.json"))
db <- load_database()
relationships <- load_relationships()
history <- source$history
plan <- source$currentPlan
profile <- source$profile
target <- source$target
as_of <- source$asOf
stopifnot(!is.null(history), !is.null(plan), !is.null(profile),
          !is.null(target), !is.null(as_of))

state_request <- list(schemaVersion = "0.1.0", requestId = "example-derive-state",
                      operation = "derive_state", history = history, target = target,
                      asOf = as_of, historyWindow = "last_28_days")
state_result <- process_training_request(state_request, db, relationships)
stopifnot(identical(state_result$status, "state_derived"))
state <- state_result$trainingState
cat("state:", state$subjectId, "at", state$asOf, "\n")

progression_result <- process_training_request(
  list(schemaVersion = "0.1.0", requestId = "example-suggest-progression",
       operation = "suggest_progression", plan = plan, trainingState = state),
  db, relationships)
if (identical(progression_result$status, "progression_available")) {
  print(progression_result$coachDecisions)
} else if (identical(progression_result$status, "insufficient_data")) {
  cat("progression: insufficient_data\n")
} else stop("progression request failed: ", progression_result$status)

adaptation_result <- process_training_request(
  list(schemaVersion = "0.1.0", requestId = "example-adapt-plan",
       operation = "adapt_plan", profile = profile, target = target,
       history = history, currentPlan = plan, asOf = as_of,
       options = source$options), db, relationships)
if (identical(adaptation_result$status, "no_change")) {
  cat("adaptation: no_change\n")
} else if (adaptation_result$status %in% c("revision_proposed", "regeneration_proposed")) {
  stopifnot(!is.null(adaptation_result$adaptation$proposedPlan))
  cat("adaptation:", adaptation_result$status, "\n")
  print(adaptation_result$adaptation$decisions)
  print(adaptation_result$adaptation$proposedPlan)
} else if (identical(adaptation_result$status, "insufficient_data")) {
  cat("adaptation: insufficient_data\n")
} else stop("adaptation failed: ", adaptation_result$status)
cat("DB++ proposes only; the host app reviews, persists, approves, and activates revisions.\n")
