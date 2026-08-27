#' Read-only Free Exercise DB++ research helpers.

`%||%` <- function(x, y) if (is.null(x)) y else x
.strings <- function(x) as.character(unlist(x %||% character(), use.names = FALSE))

load_database <- function(path) {
  stopifnot(length(path) == 1L)
  document <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (is.null(document$exercises) || !is.list(document$exercises)) stop("database is missing exercises")
  structure(list(metadata = document$metadata %||% list(), exercises = document$exercises), class = "fedbpp_database")
}

load_relationships <- function(path) {
  stopifnot(length(path) == 1L)
  document <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (is.null(document$families) || is.null(document$relationships)) stop("relationship artifact is missing families or relationships")
  structure(document, class = "fedbpp_relationships")
}

family_for <- function(relationships, exercise_id) {
  rows <- Filter(function(x) identical(x$sourceExerciseId, exercise_id) && identical(x$relationship, "member_of_family"), relationships$relationships)
  if (!length(rows)) return(NULL)
  relationships$families[[rows[[1L]]$familyId]]
}

family_members <- function(relationships, family_id) {
  sort(unique(vapply(Filter(function(x) identical(x$familyId, family_id) && identical(x$relationship, "member_of_family"), relationships$relationships), `[[`, character(1), "sourceExerciseId")))
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

# WorkoutIntent 0.1.0 -------------------------------------------------------
# These functions intentionally operate on lists, keeping JSON null versus
# omission observable to research callers while matching the Python oracle's
# resolution statuses and provenance fields.
read_workout_intent <- function(path, validate = TRUE) {
  intent <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (validate) validate_workout_intent(intent)
  class(intent) <- c("fedbpp_workout_intent", "list"); intent
}

read_intent_policies <- function() {
  path <- system.file("extdata", "intent-policies.json", package = "fedbpp")
  if (!nzchar(path) || !file.exists(path)) path <- file.path("inst", "extdata", "intent-policies.json")
  if (!file.exists(path)) path <- file.path("packages", "r", "fedbpp", "inst", "extdata", "intent-policies.json")
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

validate_workout_intent <- function(intent, database = NULL, relationships = NULL) {
  if (!is.list(intent)) return("<root>: must be an object")
  allowed <- c("schemaVersion","intentId","subjectId","goal","schedule","sessionConstraints","environment","equipmentOverrides","exerciseConstraints","preferences","continuity","useHistory","historyWindow","requestedPlanningPolicy","requestedGoalPolicy")
  errors <- setdiff(names(intent), allowed); if (length(errors)) errors <- paste0("<root>: additional property ", errors)
  if (!identical(intent$schemaVersion, "0.1.0")) errors <- c(errors, "schemaVersion: must be 0.1.0")
  schedule <- intent$schedule %||% list(); days <- unique(c(schedule$preferredWeekdays %||% character(), schedule$excludedWeekdays %||% character()))
  if (length(days) && (is.null(schedule$cycleLengthDays) || as.numeric(schedule$cycleLengthDays) != 7)) errors <- c(errors, "schedule weekday fields require cycleLengthDays of 7")
  if (length(intersect(schedule$preferredWeekdays %||% character(), schedule$excludedWeekdays %||% character()))) errors <- c(errors, "schedule: preferredWeekdays and excludedWeekdays conflict")
  if (length(intersect(schedule$preferredDayOffsets %||% integer(), schedule$excludedDayOffsets %||% integer()))) errors <- c(errors, "schedule: preferredDayOffsets and excludedDayOffsets conflict")
  range_errors <- function(r, field) { if (is.null(r)) return(character()); e <- character(); if (!is.null(r$min) && !is.null(r$max) && r$min > r$max) e <- c(e, paste0(field, ": min must not exceed max")); if (!is.null(r$min) && !is.null(r$target) && r$target < r$min) e <- c(e, paste0(field, ": target must not be below min")); if (!is.null(r$max) && !is.null(r$target) && r$target > r$max) e <- c(e, paste0(field, ": target must not exceed max")); e }
  errors <- c(errors, range_errors(schedule$sessionsPerCycle, "schedule.sessionsPerCycle"), range_errors((intent$sessionConstraints %||% list())$exercisesPerSession, "sessionConstraints.exercisesPerSession"))
  constraints <- intent$exerciseConstraints %||% list(); if (length(intersect(unique(base::c(constraints$requiredExerciseIds %||% character(), constraints$lockedExerciseIds %||% character())), constraints$excludedExerciseIds %||% character()))) errors <- base::c(errors, "exerciseConstraints: requiredExerciseIds conflicts with excludedExerciseIds")
  if (length(intersect(constraints$requiredFamilyIds %||% character(), constraints$excludedFamilyIds %||% character()))) errors <- c(errors, "exerciseConstraints: requiredFamilyIds conflicts with excludedFamilyIds")
  if (length(.strings(c(constraints$requiredFamilyIds, constraints$excludedFamilyIds, (intent$preferences %||% list())$preferredFamilyIds, (intent$preferences %||% list())$avoidedFamilyIds))) && is.null(relationships)) errors <- c(errors, "exercise family constraints require exercise relationships")
  for (pair in list(c("preferredExerciseIds", "excludedExerciseIds"), c("avoidedExerciseIds", "excludedExerciseIds"), c("preferredFamilyIds", "excludedFamilyIds"), c("avoidedFamilyIds", "excludedFamilyIds"))) if (length(intersect((intent$preferences %||% list())[[pair[[1L]]]] %||% character(), constraints[[pair[[2L]]]] %||% character()))) errors <- c(errors, paste0("preferences: ", pair[[1L]], " conflicts with ", pair[[2L]]))
  if (identical(intent$goal, "hypertrophy") && identical(intent$requestedGoalPolicy, "general-strength-v1") || identical(intent$goal, "strength") && identical(intent$requestedGoalPolicy, "general-hypertrophy-v1")) errors <- c(errors, "GOAL_POLICY_MISMATCH")
  if (!is.null(intent$requestedGoalPolicy) && !intent$requestedGoalPolicy %in% c("general-hypertrophy-v1", "general-strength-v1")) errors <- c(errors, "requestedGoalPolicy: unknown goal policy")
  if (!is.null(intent$requestedPlanningPolicy) && !intent$requestedPlanningPolicy %in% c("full-body-general-v1", "upper-lower-general-v1")) errors <- c(errors, "requestedPlanningPolicy: unknown planning policy")
  if (!is.null(intent$goal) && !intent$goal %in% c("hypertrophy", "strength", "muscular_endurance", "general_fitness", "skill_practice", "power")) errors <- c(errors, "goal: unsupported value")
  if (!is.null(intent$environment) && !intent$environment %in% c("commercial_gym", "home_gym", "minimal_equipment", "bodyweight_only", "custom")) errors <- c(errors, "environment: unsupported value")
  if (!is.null(intent$continuity) && !intent$continuity %in% c("preserve", "neutral", "vary")) errors <- c(errors, "continuity: unsupported value")
  if (!is.null(database)) {
    constraints <- intent$exerciseConstraints %||% list(); prefs <- intent$preferences %||% list()
    known <- names(database$exercises)
    unknown_messages <- function(field, values, known, suffix) {
      values <- .strings(values); unknown <- values[!values %in% known]
      if (length(unknown)) paste0(field, suffix, unknown) else character()
    }
    for (pair in list(c("requiredExerciseIds", "exerciseConstraints"), c("lockedExerciseIds", "exerciseConstraints"), c("excludedExerciseIds", "exerciseConstraints"), c("preferredExerciseIds", "preferences"), c("avoidedExerciseIds", "preferences"))) {
      values <- (if (pair[[2L]] == "exerciseConstraints") constraints else prefs)[[pair[[1L]]]] %||% character()
      errors <- c(errors, unknown_messages(pair[[1L]], values, known, ": unknown exerciseId: "))
    }
    equipment <- unique(unlist(lapply(database$exercises, function(x) x$source$equipment %||% character()), use.names = FALSE))
    overrides <- intent$equipmentOverrides %||% list()
    for (field in c("addEquipment", "removeEquipment")) {
      values <- overrides[[field]] %||% character()
      errors <- c(errors, unknown_messages(field, values, equipment, ": unknown DB++ equipment value: "))
    }
    if (!is.null(relationships)) {
      families <- names(relationships$families)
      for (field in c("requiredFamilyIds", "excludedFamilyIds")) { values <- constraints[[field]] %||% character(); errors <- c(errors, unknown_messages(field, values, families, ": unknown familyId: ")) }
      for (field in c("preferredFamilyIds", "avoidedFamilyIds")) { values <- prefs[[field]] %||% character(); errors <- c(errors, unknown_messages(field, values, families, ": unknown familyId: ")) }
    }
  }
  sort(unique(errors))
}

resolve_intent <- function(intent, db = NULL, profile = NULL, target = NULL, relationships = NULL, history = NULL, as_of = NULL) {
  doc <- if (inherits(intent, "fedbpp_workout_intent")) unclass(intent) else intent
  equipment_overrides <- doc$equipmentOverrides %||% list()
  empty_overrides <- list(goalPolicy = FALSE, planningPolicy = FALSE, target = FALSE, trainingProfile = FALSE, equipmentAdded = character(), equipmentRemoved = character())
  empty <- list(status="invalid", resolvedProfile=NULL, resolvedTarget=NULL, planningPolicy=NULL, goalPolicy=NULL, environmentPolicy=NULL, generationOptions=list(), missingInformation=list(), warnings=character(), conflicts=list(), defaultsApplied=character(), explicitOverrides=empty_overrides, provenance=list(intentSchemaVersion=doc$schemaVersion %||% NULL))
  errors <- validate_workout_intent(doc, db, relationships)
  if (length(errors)) { empty$conflicts <- lapply(errors, function(x) list(code=if (identical(x,"GOAL_POLICY_MISMATCH")) x else "INVALID_INTENT", detail=x)); return(empty) }
  s <- doc$schedule %||% list(); constraints <- doc$exerciseConstraints %||% list(); missing <- list()
  if (is.null(doc$goal)) missing <- c(missing, list(list(field="goal", reason="required_for_goal_policy_resolution")))
  if (is.null(s$cycleLengthDays)) missing <- c(missing, list(list(field="schedule.cycleLengthDays", reason="required_for_schedule_resolution")))
  if (is.null(s$sessionsPerCycle)) missing <- c(missing, list(list(field="schedule.sessionsPerCycle", reason="required_for_schedule_resolution")))
  if (is.null(doc$environment) && (is.null(profile) || is.null(profile$equipment) || !length(profile$equipment))) missing <- c(missing, list(list(field="environmentOrEquipment", reason="required_for_equipment_resolution")))
  if (identical(doc$environment, "home_gym") && (is.null(profile$equipment) || !length(profile$equipment)) && !length(equipment_overrides$addEquipment %||% character())) missing <- c(missing, list(list(field="equipmentOverrides.addEquipment", reason="home_gym_has_no_v1_preset")))
  if (identical(doc$environment, "custom") && (is.null(profile$equipment) || !length(profile$equipment)) && !length(equipment_overrides$addEquipment %||% character())) missing <- c(missing, list(list(field="equipmentOverrides.addEquipment", reason="required_for_custom_environment")))
  if (length(missing)) { empty$status <- "needs_clarification"; empty$missingInformation <- missing; return(empty) }
  goal_id <- doc$requestedGoalPolicy
  if (is.null(goal_id)) goal_id <- switch(doc$goal, hypertrophy="general-hypertrophy-v1", strength="general-strength-v1", NULL)
  if (is.null(goal_id)) { empty$status <- "needs_clarification"; empty$missingInformation <- list(list(field="requestedGoalPolicy", reason="no_default_goal_policy_for_goal")); return(empty) }
  is_strength <- identical(goal_id, "general-strength-v1"); policy_goal <- if (is_strength) "strength" else "hypertrophy"
  if (!identical(doc$goal, policy_goal)) { empty$conflicts <- list(list(code="GOAL_POLICY_MISMATCH", goal=doc$goal, requestedGoalPolicy=goal_id, policyGoal=policy_goal)); return(empty) }
  policies <- read_intent_policies(); goal_policy <- policies$goalPolicies[[goal_id]]; description <- goal_policy$description
  envs <- lapply(policies$environmentPolicies, function(value) list(id=value$policyId, equipment=unlist(value$equipment, use.names=FALSE))); names(envs) <- vapply(envs, function(value) policies$environmentPolicies[[which(vapply(policies$environmentPolicies, function(x) identical(x$policyId, value$id), logical(1)))]]$environment, character(1))
  env <- envs[[doc$environment]]; additions <- sort(unique(.strings(equipment_overrides$addEquipment))); removals <- sort(unique(.strings(equipment_overrides$removeEquipment)))
  profile_has_equipment <- !is.null(profile$equipment) && length(profile$equipment) > 0; base_equipment <- if (profile_has_equipment) profile$equipment else if (!is.null(env)) env$equipment else character(); resolved_equipment <- sort(setdiff(union(base_equipment, additions), removals)); resolved_env <- if (profile_has_equipment) NULL else env
  resolved_profile <- profile %||% list(); resolved_profile$schemaVersion <- resolved_profile$schemaVersion %||% "0.1.0"; resolved_profile$profileId <- resolved_profile$profileId %||% "resolved-profile"; resolved_profile$subjectId <- doc$subjectId %||% resolved_profile$subjectId %||% NULL; resolved_profile$goals <- list(list(type=doc$goal)); resolved_profile$equipment <- resolved_equipment; resolved_profile$exercisePreferences <- resolved_profile$exercisePreferences %||% list(); prefs <- doc$preferences %||% list(); for (key in c("preferredExerciseIds", "avoidedExerciseIds", "preferredFamilyIds", "avoidedFamilyIds")) if (length(.strings(prefs[[key]]))) resolved_profile$exercisePreferences[[key]] <- sort(unique(c(.strings(resolved_profile$exercisePreferences[[key]]), .strings(prefs[[key]]))))
  av <- resolved_profile$availability %||% list(); av$cycleLengthDays <- s$cycleLengthDays; av$sessionsPerCycle <- s$sessionsPerCycle; av$preferredDayOffsets <- sort(unique(c(s$preferredDayOffsets %||% integer(), match(s$preferredWeekdays %||% character(), c("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))-1L))); av$preferredDayOffsets <- av$preferredDayOffsets[!is.na(av$preferredDayOffsets)]; av$excludedDayOffsets <- sort(unique(c(s$excludedDayOffsets %||% integer(), match(s$excludedWeekdays %||% character(), c("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))-1L))); av$excludedDayOffsets <- av$excludedDayOffsets[!is.na(av$excludedDayOffsets)]; if (!is.null(doc$sessionConstraints$exercisesPerSession)) av$exercisesPerSession <- doc$sessionConstraints$exercisesPerSession; resolved_profile$availability <- av; resolved_profile$constraints <- resolved_profile$constraints %||% list(); resolved_profile$constraints$excludedExerciseIds <- sort(unique(c(resolved_profile$constraints$excludedExerciseIds %||% character(), constraints$excludedExerciseIds %||% character()))); resolved_profile$constraints$excludedFamilyIds <- sort(unique(c(resolved_profile$constraints$excludedFamilyIds %||% character(), constraints$excludedFamilyIds %||% character())))
  muscles <- goal_policy$muscles; default_target <- list(schemaVersion="0.1.0", targetId=paste0(goal_id,"-default"), periodDays=s$cycleLengthDays, muscles=muscles, notes=description); resolved_target <- merge_target(default_target, target)
  target_errors <- validate_target(resolved_target); if (length(target_errors)) { empty$resolvedTarget <- resolved_target; empty$conflicts <- lapply(target_errors, function(x) list(code="TARGET_OVERRIDE_CONFLICT", detail=x)); return(empty) }
  required_exercises <- unique(c(.strings(constraints$requiredExerciseIds), .strings(constraints$lockedExerciseIds))); excluded_exercises <- .strings(resolved_profile$constraints$excludedExerciseIds); required_families <- .strings(constraints$requiredFamilyIds); excluded_families <- .strings(resolved_profile$constraints$excludedFamilyIds)
  constraint_conflicts <- c(lapply(sort(intersect(required_exercises, excluded_exercises)), function(x) list(code="REQUIRED_EXERCISE_EXCLUDED", exerciseId=x)), lapply(sort(intersect(required_families, excluded_families)), function(x) list(code="REQUIRED_FAMILY_EXCLUDED", familyId=x)))
  if (length(constraint_conflicts)) { empty$resolvedProfile <- resolved_profile; empty$resolvedTarget <- resolved_target; empty$conflicts <- constraint_conflicts; return(empty) }
  defaults <- c(if (is.null(doc$requestedGoalPolicy)) "goalPolicy", if (is.null(doc$requestedPlanningPolicy)) "planningPolicy", if (!is.null(resolved_env)) "environmentPolicy")
  options <- list(continuity=doc$continuity %||% "neutral", repDefaults=goal_policy$reps, effortDefaults=goal_policy$effort, requiredFamilyIds=sort(unique(.strings(constraints$requiredFamilyIds))))
  warnings <- character(); if (isTRUE(doc$useHistory) && is.null(history)) warnings <- c(warnings, "useHistory was requested but no history was provided"); if (isTRUE(doc$useHistory) && !is.null(history) && is.null(as_of)) warnings <- c(warnings, "useHistory was requested but as_of is required to derive TrainingState")
  if (isTRUE(doc$useHistory) && !is.null(history) && !is.null(as_of)) options$trainingState <- derive_training_state(history, as_of)
  dbmd <- db$metadata %||% list(); rel_version <- if (!is.null(relationships)) relationships$schemaVersion %||% NULL else NULL
  list(status=if(length(defaults)) "resolved_with_defaults" else "resolved", resolvedProfile=resolved_profile, resolvedTarget=resolved_target, planningPolicy=doc$requestedPlanningPolicy %||% "full-body-general-v1", goalPolicy=list(policyId=goal_id, policyVersion="1", description=description), environmentPolicy=if(!is.null(resolved_env)) resolved_env$id else NULL, generationOptions=options, missingInformation=list(), warnings=warnings, conflicts=list(), defaultsApplied=defaults, explicitOverrides=list(goalPolicy=!is.null(doc$requestedGoalPolicy), planningPolicy=!is.null(doc$requestedPlanningPolicy), target=!is.null(target), trainingProfile=!is.null(profile), equipmentAdded=additions, equipmentRemoved=removals), provenance=list(intentSchemaVersion=doc$schemaVersion, goalPolicy=list(policyId=goal_id, policyVersion="1"), environmentPolicy=if(!is.null(resolved_env)) list(policyId=resolved_env$id, policyVersion="1") else NULL, dbSchemaVersion=dbmd$schemaVersion %||% NULL, dbConverterVersion=dbmd$converterVersion %||% NULL, relationshipSchemaVersion=rel_version))
}

derive_training_state <- function(history, as_of) {
  as_date <- as.Date(substr(as_of, 1L, 10L)); start_date <- as_date - 27L
  workouts <- Filter(function(w) {
    if (is.null(w$startTime)) return(FALSE)
    stamp <- as.POSIXct(w$startTime, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
    !is.na(stamp) && as.Date(stamp) >= start_date && w$startTime <= as_of
  }, history$workouts %||% list())
  state <- list()
  for (workout in workouts) for (exercise in workout$exercises %||% list()) {
    id <- exercise$exerciseId %||% NULL; if (is.null(id)) next
    completed <- sum(vapply(exercise$sets %||% list(), function(x) isTRUE(x$completed), logical(1)))
    previous <- state[[id]] %||% list(exerciseId = id, recentSessionCount = 0L, recentCompletedSetCount = 0L)
    state[[id]] <- list(exerciseId = id, recentSessionCount = previous$recentSessionCount + 1L, recentCompletedSetCount = previous$recentCompletedSetCount + completed)
  }
  active <- NULL
  for (plan in history$plans %||% list()) for (activation in history$planActivations %||% list()) if (identical(plan$planId, activation$planId) && identical(plan$revisionId, activation$revisionId) && !is.null(activation$effectiveFrom) && activation$effectiveFrom <= as_of && (is.null(activation$effectiveTo) || as_of < activation$effectiveTo)) active <- plan
  active_plan <- list()
  if (!is.null(active)) {
    activation <- Filter(function(x) identical(x$planId, active$planId) && identical(x$revisionId, active$revisionId), history$planActivations %||% list())[[1L]]
    cycle <- as.integer(active$cycle$lengthDays %||% 7L); elapsed <- max(0L, as.integer(as_date - as.Date(substr(activation$effectiveFrom, 1L, 10L))))
    active_plan <- list(planId = active$planId, revisionId = active$revisionId, phaseId = NULL, cyclePosition = elapsed %% cycle + 1L)
  }
  window <- list(type = "last_28_days", start = as.character(start_date), end = as.character(as_date))
  list(stateVersion = "0.1.0", subjectId = history$subjectId %||% NULL, asOf = as_of, historyWindow = window, activePlan = active_plan, exerciseState = state, familyState = list(), muscleState = list(), adherenceState = list(), sessionState = list(), provenance = list(stateVersion = "0.1.0", asOf = as_of, historyWindow = window))
}

generate_plan_from_intent <- function(intent, db, profile = NULL, target = NULL, relationships = NULL, history = NULL, as_of = NULL, ...) {
  resolution <- resolve_intent(intent, db, profile, target, relationships, history, as_of)
  if (!resolution$status %in% c("resolved", "resolved_with_defaults")) return(list(resolution = resolution, generation = NULL))
  availability <- resolution$resolvedProfile$availability; n <- as.integer((availability$sessionsPerCycle$target %||% availability$sessionsPerCycle$min %||% 1)); k <- as.integer(availability$exercisesPerSession$target %||% 3)
  constraints <- intent$exerciseConstraints %||% list(); excluded <- unique(.strings(constraints$excludedExerciseIds)); required <- unique(c(.strings(constraints$requiredExerciseIds), .strings(constraints$lockedExerciseIds)))
  available <- sort(names(db$exercises)); allowed <- available[!available %in% excluded]
  ids <- unique(c(required, allowed))[seq_len(min(max(1L, k), length(unique(c(required, allowed)))))]
  preferred <- as.integer(unlist(availability$preferredDayOffsets %||% integer(), use.names = FALSE)); excluded_days <- as.integer(unlist(availability$excludedDayOffsets %||% integer(), use.names = FALSE)); cycle <- as.integer(availability$cycleLengthDays %||% 7L)
  offsets <- unique(c(preferred, seq_len(cycle) - 1L)); offsets <- offsets[!offsets %in% excluded_days]; offsets <- offsets[seq_len(min(max(1L, n), length(offsets)))]
  sessions <- lapply(seq_along(offsets), function(i) list(planSessionId = paste0("intent-session-", i), dayOffset = offsets[[i]], exercises = lapply(seq_along(ids), function(j) list(prescriptionId = paste0("intent-rx-", i, "-", j), exerciseId = ids[[j]], order = j, sets = 1L, reps = resolution$generationOptions$repDefaults))))
  list(resolution = resolution, generation = list(status = "generated", schemaVersion = "0.2.0", sessions = sessions))
}

merge_target <- function(default, explicit = NULL) {
  if (is.null(explicit)) return(default)
  result <- default
  merge_section <- function(left, right) { if (is.null(left)) left <- list(); for (key in names(right)) left[[key]] <- if (is.list(right[[key]]) && is.list(left[[key]])) modifyList(left[[key]], right[[key]]) else right[[key]]; left }
  for (key in names(explicit)) {
    if (key %in% c("muscles", "movementPatterns", "families")) result[[key]] <- merge_section(result[[key]], explicit[[key]])
    else if (identical(key, "frequency")) { result$frequency <- result$frequency %||% list(); result$frequency$muscles <- merge_section(result$frequency$muscles, explicit[[key]]$muscles %||% list()) }
    else result[[key]] <- explicit[[key]]
  }
  result
}

validate_target <- function(target) {
  errors <- character(); check <- function(section, values, keys) { if (is.null(values)) return(character()); out <- character(); for (name in names(values)) { r <- values[[name]]; if (!is.null(r[[keys[1]]]) && !is.null(r[[keys[3]]]) && r[[keys[1]]] > r[[keys[3]]]) out <- c(out, paste0(section, ".", name, ": min must not exceed max")); if (!is.null(r[[keys[1]]]) && !is.null(r[[keys[2]]]) && r[[keys[2]]] < r[[keys[1]]]) out <- c(out, paste0(section, ".", name, ": target must not be below min")); if (!is.null(r[[keys[3]]]) && !is.null(r[[keys[2]]]) && r[[keys[2]]] > r[[keys[3]]]) out <- c(out, paste0(section, ".", name, ": target must not exceed max")) }; out }
  errors <- c(errors, check("muscles", target$muscles, c("min", "target", "max")), check("frequency.muscles", (target$frequency %||% list())$muscles, c("min", "target", "max")), check("movementPatterns", target$movementPatterns, c("minimumSets", "targetSets", "maximumSets")), check("families", target$families, c("minimumSets", "targetSets", "maximumSets")))
  sort(unique(errors))
}
