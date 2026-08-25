#' Read-only Free Exercise DB++ research helpers.

`%||%` <- function(x, y) if (is.null(x)) y else x

load_database <- function(path) {
  stopifnot(length(path) == 1L)
  document <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (is.null(document$exercises) || !is.list(document$exercises)) stop("database is missing exercises")
  structure(list(metadata = document$metadata %||% list(), exercises = document$exercises), class = "fedbpp_database")
}

load_workout <- function(path, validate = TRUE) {
  workout <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (validate) validate_workout(workout)
  class(workout) <- c("fedbpp_workout", "list")
  workout
}

validate_workout <- function(workout) {
  required <- c("schemaVersion", "sessionId", "startTime", "exercises")
  if (!all(required %in% names(workout))) stop("workout missing required fields")
  if (!identical(workout$schemaVersion, "0.2.0")) stop("unsupported workout schema")
  if (!is.character(workout$sessionId) || !nzchar(workout$sessionId)) stop("sessionId must not be blank")
  if (!is.list(workout$exercises)) stop("exercises must be an array")
  invisible(TRUE)
}

migrate_workout <- function(workout) {
  version <- workout$schemaVersion
  if (identical(version, "0.2.0")) return(workout)
  if (!is.character(version) || !startsWith(version, "0.1.")) stop("unsupported workout schema")
  result <- workout
  result$schemaVersion <- "0.2.0"
  result$exercises <- lapply(result$exercises %||% list(), function(exercise) {
    exercise$laterality <- exercise$laterality %||% "unspecified"
    exercise$sets <- lapply(exercise$sets %||% list(), function(set) {
      set$laterality <- set$laterality %||% NULL
      set
    })
    exercise
  })
  result
}

effective_sets <- function(workout, database) {
  validate_workout(workout)
  rows <- list()
  for (observation in workout$exercises) {
    id <- observation$exerciseId %||% NULL
    if (is.null(id) || is.null(database$exercises[[id]])) next
    exercise <- database$exercises[[id]]
    annotation <- exercise$annotation %||% list()
    if (!isTRUE(annotation$volumeEligible)) next
    counted_types <- c("working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted")
    completed <- vapply(observation$sets %||% list(), function(set) isTRUE(set$completed) && (set$setType %||% "working") %in% counted_types, logical(1))
    n <- sum(completed)
    credits <- database$metadata$setCredits %||% list(direct = 1, indirect = 0.5, stabilizer = 0)
    confidence <- annotation$confidence %||% NA_character_
    for (muscle in unlist(annotation$direct %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$direct, credit = credits$direct, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
    for (muscle in unlist(annotation$indirect %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$indirect, credit = credits$indirect, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
    for (muscle in unlist(annotation$stabilizers %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$stabilizer, credit = credits$stabilizer, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
  }
  if (!length(rows)) return(data.frame(muscle = character(), effective_sets = numeric(), credit = numeric(), exercise_id = character(), confidence = character(), stringsAsFactors = FALSE))
  do.call(rbind, rows)
}

workout_observations <- function(workout) {
  validate_workout(workout)
  rows <- lapply(workout$exercises, function(exercise) {
    data.frame(exercise_id = exercise$exerciseId %||% NA_character_, exercise_name = exercise$exerciseName %||% NA_character_, order = exercise$order %||% NA_integer_, set_count = length(exercise$sets %||% list()), stringsAsFactors = FALSE)
  })
  if (!length(rows)) data.frame(exercise_id = character(), exercise_name = character(), order = integer(), set_count = integer(), stringsAsFactors = FALSE) else do.call(rbind, rows)
}

longitudinal_volume <- function(workouts, database) {
  if (inherits(workouts, "fedbpp_workout") || (is.list(workouts) && "schemaVersion" %in% names(workouts))) workouts <- list(workouts)
  rows <- lapply(workouts, function(workout) {
    totals <- effective_sets(workout, database)
    if (!nrow(totals)) return(data.frame(session_id = workout$sessionId %||% NA_character_, start_time = workout$startTime %||% NA_character_, muscle = character(), effective_sets = numeric(), stringsAsFactors = FALSE))
    data.frame(session_id = workout$sessionId %||% NA_character_, start_time = workout$startTime %||% NA_character_, aggregate(totals$effective_sets, list(totals$muscle), sum), stringsAsFactors = FALSE)
  })
  if (!length(rows)) return(data.frame(session_id = character(), start_time = character(), muscle = character(), effective_sets = numeric(), stringsAsFactors = FALSE))
  result <- do.call(rbind, rows); names(result)[3:4] <- c("muscle", "effective_sets"); result
}
